"""
Accounting API endpoints
Provides daily Net calculation used by the Accounting → Net tab
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func, text
from datetime import datetime
from decimal import Decimal
import logging

from app import db, limiter
from app.models.transaction import Transaction
from app.models.financial import DailyNet, Expense, ExpenseBudget, MonthlyCurrencySummary
from flask_login import current_user
from datetime import timedelta
from app.utils.tenant_helpers import set_tenant_on_new_record, add_tenant_filter, validate_tenant_access

logger = logging.getLogger(__name__)

accounting_api = Blueprint('accounting_api', __name__)

# CSRF protection is handled via @require_csrf decorator on critical endpoints
from app import csrf
csrf.exempt(accounting_api)  # Still exempt blueprint, but use @require_csrf on critical routes
from app.utils.csrf_decorator import require_csrf

# Test endpoint to verify routing works
@accounting_api.route("/test", methods=["GET"])
@login_required
def test_accounting_endpoint():
    """Test endpoint to verify accounting API routing"""
    return jsonify({
        "success": True,
        "message": "Accounting API is working",
        "endpoint": "/api/v1/accounting/test"
    }), 200

@accounting_api.route("/expenses", methods=["GET"])  # /api/v1/accounting/expenses
@login_required
def get_expenses():
    """Get all expenses with advanced filtering - with comprehensive error handling and logging"""
    try:
        # Check if expense table exists, create if it doesn't
        try:
            # Try to query the table to see if it exists
            db.session.execute(text("SELECT 1 FROM expense LIMIT 1"))
        except Exception as table_error:
            # Table doesn't exist, create it
            error_str = str(table_error).lower()
            if "no such table" in error_str or "does not exist" in error_str or "table" in error_str:
                logger.info("Expense table not found, creating it...")
                try:
                    # Try using SQLAlchemy table creation
                    Expense.__table__.create(db.engine, checkfirst=True)
                    db.session.commit()
                    logger.info("Expense table created successfully using SQLAlchemy")
                except Exception as create_error:
                    logger.error(f"Failed to create expense table with SQLAlchemy: {create_error}, trying raw SQL...")
                    # Fallback: try raw SQL
                    try:
                        create_sql = """
                        CREATE TABLE IF NOT EXISTS expense (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            description VARCHAR(200) NOT NULL,
                            detail TEXT,
                            amount_try NUMERIC(15, 2) NOT NULL DEFAULT 0.0,
                            amount_usd NUMERIC(15, 2) NOT NULL DEFAULT 0.0,
                            status VARCHAR(20) NOT NULL DEFAULT 'pending',
                            cost_period VARCHAR(50),
                            payment_date DATE,
                            payment_period VARCHAR(50),
                            source VARCHAR(100),
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            created_by INTEGER,
                            FOREIGN KEY (created_by) REFERENCES user(id)
                        );
                        """
                        db.session.execute(text(create_sql))
                        db.session.commit()
                        logger.info("Expense table created successfully using raw SQL")
                    except Exception as sql_error:
                        logger.error(f"Failed to create expense table with raw SQL: {sql_error}")
                        return jsonify({
                            "success": False,
                            "error": f"Database table not found and could not be created. Please run the migration: {str(sql_error)}",
                            "expenses": []
                        }), 500
        
        # Build query with filters
        query = Expense.query
        
        # Multi-tenancy: Apply organization filter
        query = add_tenant_filter(query, Expense)
        
        # Filter by status
        status = request.args.get("status")
        if status:
            query = query.filter(Expense.status == status)
        
        # Filter by category
        category = request.args.get("category")
        if category:
            query = query.filter(Expense.category == category)
        
        # Filter by type
        expense_type = request.args.get("type")
        if expense_type:
            query = query.filter(Expense.type == expense_type)
        
        # Filter by cost period
        cost_period = request.args.get("cost_period")
        if cost_period:
            query = query.filter(Expense.cost_period == cost_period)
        
        # Filter by date range
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")
        if date_from:
            try:
                start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
                query = query.filter(Expense.payment_date >= start_date)
            except ValueError:
                pass
        if date_to:
            try:
                end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
                query = query.filter(Expense.payment_date <= end_date)
            except ValueError:
                pass
        
        # Search in description, detail, and source
        search = request.args.get("search")
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Expense.description.ilike(search_pattern),
                    Expense.detail.ilike(search_pattern),
                    Expense.source.ilike(search_pattern)
                )
            )
        
        # Sort options
        sort_by = request.args.get("sort_by", "created_at")
        sort_order = request.args.get("sort_order", "desc")
        
        # Map sort_by to actual column
        sort_column = getattr(Expense, sort_by, Expense.created_at)
        
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Execute query
        expenses = query.all()
        
        return jsonify({
            "success": True,
            "expenses": [expense.to_dict() for expense in expenses],
            "count": len(expenses),
            "filters_applied": {
                "status": status,
                "category": category,
                "type": expense_type,
                "cost_period": cost_period,
                "date_from": date_from,
                "date_to": date_to,
                "search": search,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        })
    except Exception as e:
        logger.error(f"Error in get_expenses: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "expenses": []
        }), 500


@accounting_api.route("/expenses/daily", methods=["GET"])  # /api/v1/accounting/expenses/daily?date=YYYY-MM-DD
@login_required
def get_daily_expenses():
    """Get daily expenses in USD for a given date from saved DailyNet records"""
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"success": False, "error": "Missing required 'date' query parameter (YYYY-MM-DD)"}), 400

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Check if saved data exists for this date
    saved_net = DailyNet.query.filter_by(date=target_date).first()
    
    if saved_net:
        return jsonify({
            "success": True,
            "data": {
                "date": target_date.isoformat(),
                "expenses_usd": float(saved_net.expenses_usd) if saved_net.expenses_usd else 0.0
            }
        })
    else:
        # No saved data for this date
        return jsonify({
            "success": True,
            "data": {
                "date": target_date.isoformat(),
                "expenses_usd": 0.0
            }
        })


@accounting_api.route("/expenses", methods=["POST"])  # /api/v1/accounting/expenses
@limiter.limit("30 per minute, 200 per hour")  # Rate limiting for data modification
@require_csrf
@login_required
def create_expense():
    """Create a new expense"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Missing request body"}), 400
        
        # Validate required fields
        if not data.get('description'):
            return jsonify({"success": False, "error": "Description is required"}), 400
        
        # Validate category
        category = data.get('category', 'inflow')
        if category not in ['inflow', 'outflow']:
            return jsonify({"success": False, "error": "Category must be 'inflow' or 'outflow'"}), 400
        
        # Validate type
        expense_type = data.get('type', 'payment')
        if expense_type not in ['payment', 'transfer']:
            return jsonify({"success": False, "error": "Type must be 'payment' or 'transfer'"}), 400
        
        # Validate mount_currency
        mount_currency = data.get('mount_currency', '')
        if mount_currency and mount_currency not in ['TRY', 'USD', 'USDT']:
            return jsonify({"success": False, "error": "Mount currency must be 'TRY', 'USD', or 'USDT'"}), 400
        
        # Parse payment_date if provided
        payment_date = None
        if data.get('payment_date'):
            try:
                payment_date = datetime.strptime(data['payment_date'], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"success": False, "error": "Invalid payment_date format. Use YYYY-MM-DD"}), 400
        
        # Create expense
        expense = Expense(
            description=data.get('description', ''),
            detail=data.get('detail', ''),
            category=category,
            type=expense_type,
            amount_try=_to_decimal(data.get('amount_try', 0)),
            amount_usd=_to_decimal(data.get('amount_usd', 0)),
            amount_usdt=_to_decimal(data.get('amount_usdt', 0)),
            mount_currency=mount_currency if mount_currency else None,
            status=data.get('status', 'pending'),
            cost_period=data.get('cost_period', ''),
            payment_date=payment_date,
            payment_period=data.get('payment_period', ''),
            source=data.get('source', ''),
            created_by=current_user.id if current_user.is_authenticated else None
        )
        
        # Multi-tenancy: Set organization_id automatically
        set_tenant_on_new_record(expense)
        
        db.session.add(expense)
        db.session.commit()
        
        logger.info(f"Created expense {expense.id} by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
        
        return jsonify({
            "success": True,
            "message": "Expense created successfully",
            "expense": expense.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating expense: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to create expense: {str(e)}"
        }), 500


@accounting_api.route("/expenses/<int:expense_id>", methods=["PUT"])  # /api/v1/accounting/expenses/<id>
@limiter.limit("30 per minute, 200 per hour")  # Rate limiting for data modification
@require_csrf
@login_required
def update_expense(expense_id):
    """Update an existing expense"""
    try:
        expense = Expense.query.get_or_404(expense_id)
        
        # Multi-tenancy: Validate access
        is_valid, error = validate_tenant_access(expense, "expense")
        if not is_valid:
            return error
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "Missing request body"}), 400
        
        # Update fields
        if 'description' in data:
            expense.description = data['description']
        if 'detail' in data:
            expense.detail = data.get('detail', '')
        if 'category' in data:
            if data['category'] not in ['inflow', 'outflow']:
                return jsonify({"success": False, "error": "Category must be 'inflow' or 'outflow'"}), 400
            expense.category = data['category']
        if 'type' in data:
            if data['type'] not in ['payment', 'transfer']:
                return jsonify({"success": False, "error": "Type must be 'payment' or 'transfer'"}), 400
            expense.type = data['type']
        if 'amount_try' in data:
            expense.amount_try = _to_decimal(data.get('amount_try', 0))
        if 'amount_usd' in data:
            expense.amount_usd = _to_decimal(data.get('amount_usd', 0))
        if 'amount_usdt' in data:
            expense.amount_usdt = _to_decimal(data.get('amount_usdt', 0))
        if 'mount_currency' in data:
            mount_currency = data.get('mount_currency', '')
            if mount_currency and mount_currency not in ['TRY', 'USD', 'USDT']:
                return jsonify({"success": False, "error": "Mount currency must be 'TRY', 'USD', or 'USDT'"}), 400
            expense.mount_currency = mount_currency if mount_currency else None
        if 'status' in data:
            expense.status = data['status']
        if 'cost_period' in data:
            expense.cost_period = data.get('cost_period', '')
        if 'payment_date' in data:
            if data['payment_date']:
                try:
                    expense.payment_date = datetime.strptime(data['payment_date'], "%Y-%m-%d").date()
                except ValueError:
                    return jsonify({"success": False, "error": "Invalid payment_date format. Use YYYY-MM-DD"}), 400
            else:
                expense.payment_date = None
        if 'payment_period' in data:
            expense.payment_period = data.get('payment_period', '')
        if 'source' in data:
            expense.source = data.get('source', '')
        
        expense.updated_at = datetime.now()
        db.session.commit()
        
        logger.info(f"Updated expense {expense_id} by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
        
        return jsonify({
            "success": True,
            "message": "Expense updated successfully",
            "expense": expense.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating expense {expense_id}: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to update expense: {str(e)}"
        }), 500


@accounting_api.route("/expenses/<int:expense_id>", methods=["DELETE"])  # /api/v1/accounting/expenses/<id>
@limiter.limit("20 per minute, 100 per hour")  # Stricter rate limiting for deletions
@require_csrf
@login_required
def delete_expense(expense_id):
    """Delete an expense"""
    try:
        expense = Expense.query.get_or_404(expense_id)
        
        # Multi-tenancy: Validate access
        is_valid, error = validate_tenant_access(expense, "expense")
        if not is_valid:
            return error
        
        db.session.delete(expense)
        db.session.commit()
        
        logger.info(f"Deleted expense {expense_id} by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
        
        return jsonify({
            "success": True,
            "message": "Expense deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting expense {expense_id}: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to delete expense: {str(e)}"
        }), 500


def _to_decimal(value, default: Decimal = Decimal('0')) -> Decimal:
    try:
        if value is None:
            return default
        return Decimal(str(value))
    except Exception:
        return default


@accounting_api.route("/crypto-balance", methods=["GET"])  # /api/v1/accounting/crypto-balance
@login_required
def get_crypto_balance():
    """Get total crypto balance from all active Trust wallets in USD"""
    try:
        from app.services.trust_wallet_service import TrustWalletService
        from app.models.trust_wallet import TrustWallet
        
        # Get all active wallets
        active_wallets = TrustWallet.query.filter_by(is_active=True).all()
        
        if not active_wallets:
            return jsonify({
                "success": True,
                "data": {
                    "total_usd": 0.0,
                    "wallets": [],
                    "wallet_count": 0
                }
            })
        
        service = TrustWalletService()
        total_usd = 0.0
        wallet_balances = []
        
        # Fetch balance for each active wallet
        for wallet in active_wallets:
            try:
                balance_data = service.get_wallet_balance(wallet.id)
                wallet_total_usd = balance_data.get('total_usd', 0.0)
                total_usd += wallet_total_usd
                
                wallet_balances.append({
                    'wallet_id': wallet.id,
                    'wallet_name': wallet.wallet_name,
                    'network': wallet.network,
                    'total_usd': wallet_total_usd,
                    'balances': balance_data.get('balances', {})
                })
                
            except Exception as wallet_err:
                logger.error(f"Error fetching balance for wallet {wallet.id}: {wallet_err}")
                # Continue with other wallets even if one fails
                wallet_balances.append({
                    'wallet_id': wallet.id,
                    'wallet_name': wallet.wallet_name,
                    'network': wallet.network,
                    'total_usd': 0.0,
                    'error': str(wallet_err)
                })
        
        return jsonify({
            "success": True,
            "data": {
                "total_usd": round(total_usd, 2),
                "wallets": wallet_balances,
                "wallet_count": len(active_wallets),
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting crypto balance: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@accounting_api.route("/net", methods=["GET"])  # /api/v1/accounting/net?date=YYYY-MM-DD
@login_required
def get_daily_net():
    """Return daily Net metrics in USD for a given date.
    Loads saved values if they exist, otherwise calculates from transactions.

    Formula (from Excel):
      NET_SAGLAMA = NET_CASH - HARCAMALAR - GIDERLER(KOMISYON) + DEVIR

    Definitions:
      - NET_CASH: Sum of USD deposits minus USD withdrawals using Transaction.amount
      - GIDERLER(KOMISYON): Sum of USD commissions for the day
      - HARCAMALAR: Daily expenses in USD (optional client-provided for now)
      - DEVREDEN TAHSILAT: Rollover amount from previous day in USD (optional)
    """
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"success": False, "error": "Missing required 'date' query parameter (YYYY-MM-DD)"}), 400

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Check if saved data exists for this date
    saved_net = DailyNet.query.filter_by(date=target_date).first()
    
    # Optional overrides supplied by client for initial iteration
    expenses_usd_param = request.args.get("expenses_usd")
    rollover_usd_param = request.args.get("rollover_usd")
    
    # Optional overrides for NET_CASH and GIDERLER(KOMISYON)
    net_cash_override = request.args.get("net_cash_usd")
    commission_override = request.args.get("commissions_usd")
    
    # New field overrides
    onceki_kapanis_param = request.args.get("onceki_kapanis_usd")
    company_cash_param = request.args.get("company_cash_usd")
    crypto_balance_param = request.args.get("crypto_balance_usd")
    anlik_kasa_param = request.args.get("anlik_kasa_usd")
    anlik_kasa_manual_param = request.args.get("anlik_kasa_manual", "false").lower() == "true"
    bekleyen_tahsilat_param = request.args.get("bekleyen_tahsilat_usd")

    # If saved data exists and no overrides provided, use saved values
    if saved_net and not net_cash_override and not commission_override and not expenses_usd_param and not rollover_usd_param and not onceki_kapanis_param and not company_cash_param and not crypto_balance_param and not anlik_kasa_param and not bekleyen_tahsilat_param:
        return jsonify({
            "success": True,
            "data": saved_net.to_dict(),
            "is_saved": True
        })

    # Query USD transactions for the target date
    # Use raw amounts for NET_CASH (deposits positive, withdrawals negative)
    amounts_row = (
        db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0),
        )
        .filter(Transaction.date == target_date, Transaction.currency == 'USD')
        .first()
    )

    commissions_row = (
        db.session.query(
            func.coalesce(func.sum(Transaction.commission), 0),
        )
        .filter(Transaction.date == target_date, Transaction.currency == 'USD')
        .first()
    )

    # Use override if provided, otherwise use saved value, otherwise use calculated value
    if net_cash_override:
        net_cash_usd = _to_decimal(net_cash_override)
    elif saved_net:
        net_cash_usd = _to_decimal(saved_net.net_cash_usd)
    else:
        net_cash_usd = _to_decimal(amounts_row[0])
    
    if commission_override:
        total_commission_usd = _to_decimal(commission_override)
    elif saved_net:
        total_commission_usd = _to_decimal(saved_net.commissions_usd)
    else:
        total_commission_usd = _to_decimal(commissions_row[0])
    
    # Use saved values if no override provided
    if saved_net:
        expenses_usd = _to_decimal(expenses_usd_param) if expenses_usd_param else _to_decimal(saved_net.expenses_usd)
        rollover_usd = _to_decimal(rollover_usd_param) if rollover_usd_param else _to_decimal(saved_net.rollover_usd)
        onceki_kapanis_usd = _to_decimal(onceki_kapanis_param) if onceki_kapanis_param else _to_decimal(saved_net.onceki_kapanis_usd)
        company_cash_usd = _to_decimal(company_cash_param) if company_cash_param else _to_decimal(saved_net.company_cash_usd)
        crypto_balance_usd = _to_decimal(crypto_balance_param) if crypto_balance_param else _to_decimal(saved_net.crypto_balance_usd)
        # Handle anlik_kasa_usd - check if manual override is active
        if anlik_kasa_param:
            anlik_kasa_usd = _to_decimal(anlik_kasa_param)
        else:
            anlik_kasa_usd = _to_decimal(saved_net.anlik_kasa_usd)
            # If saved data has manual override, use it; otherwise check if we should auto-calculate
            if not saved_net.anlik_kasa_manual:
                # Recalculate if company_cash or crypto_balance changed
                if company_cash_param or crypto_balance_param:
                    company_cash = _to_decimal(company_cash_param) if company_cash_param else _to_decimal(saved_net.company_cash_usd)
                    crypto_balance = _to_decimal(crypto_balance_param) if crypto_balance_param else _to_decimal(saved_net.crypto_balance_usd)
                    anlik_kasa_usd = company_cash + crypto_balance
                    anlik_kasa_manual_param = False
            else:
                # Manual mode is active in saved data
                anlik_kasa_manual_param = True
        
        bekleyen_tahsilat_usd = _to_decimal(bekleyen_tahsilat_param) if bekleyen_tahsilat_param else _to_decimal(saved_net.bekleyen_tahsilat_usd)
    else:
        expenses_usd = _to_decimal(expenses_usd_param) if expenses_usd_param else Decimal('0')
        rollover_usd = _to_decimal(rollover_usd_param) if rollover_usd_param else Decimal('0')
        
        # For onceki_kapanis, try to get from previous day's anlik_kasa if not provided
        if onceki_kapanis_param:
            onceki_kapanis_usd = _to_decimal(onceki_kapanis_param)
        else:
            from datetime import timedelta
            previous_date = target_date - timedelta(days=1)
            previous_net = DailyNet.query.filter_by(date=previous_date).first()
            onceki_kapanis_usd = _to_decimal(previous_net.anlik_kasa_usd) if previous_net else Decimal('0')
        
        company_cash_usd = _to_decimal(company_cash_param) if company_cash_param else Decimal('0')
        crypto_balance_usd = _to_decimal(crypto_balance_param) if crypto_balance_param else Decimal('0')
        
        # Calculate anlik_kasa_usd = company_cash_usd + crypto_balance_usd
        # Unless explicitly provided as override (manual mode)
        if anlik_kasa_param:
            anlik_kasa_usd = _to_decimal(anlik_kasa_param)
        else:
            anlik_kasa_usd = company_cash_usd + crypto_balance_usd
            anlik_kasa_manual_param = False  # Auto-calculated
        
        bekleyen_tahsilat_usd = _to_decimal(bekleyen_tahsilat_param) if bekleyen_tahsilat_param else Decimal('0')

    # NET SAGLAMA calculation
    # NET_SAGLAMA = NET_CASH - EXPENSES - COMMISSION + ROLLOVER
    net_saglama_usd = net_cash_usd - expenses_usd - total_commission_usd + rollover_usd
    
    # FARK calculation: ANLIK KASA - ÖNCEKİ KAPANIŞ + BEKLEYEN TAHSİLAT
    fark_usd = anlik_kasa_usd - onceki_kapanis_usd + bekleyen_tahsilat_usd
    
    # FARK (bottom) calculation: FARK - NET SAGLAMA
    fark_bottom_usd = fark_usd - net_saglama_usd

    response = {
        "success": True,
        "data": {
            "date": target_date.isoformat(),
            "net_cash_usd": float(net_cash_usd),
            "expenses_usd": float(expenses_usd),
            "commissions_usd": float(total_commission_usd),
            "rollover_usd": float(rollover_usd),
            "net_saglama_usd": float(net_saglama_usd),
            "onceki_kapanis_usd": float(onceki_kapanis_usd),
            "company_cash_usd": float(company_cash_usd),
            "crypto_balance_usd": float(crypto_balance_usd),
            "anlik_kasa_usd": float(anlik_kasa_usd),
            "anlik_kasa_manual": anlik_kasa_manual_param if anlik_kasa_param else (saved_net.anlik_kasa_manual if saved_net and not (company_cash_param or crypto_balance_param) else False),
            "bekleyen_tahsilat_usd": float(bekleyen_tahsilat_usd),
            "fark_usd": float(fark_usd),
            "fark_bottom_usd": float(fark_bottom_usd),
        },
        "is_saved": saved_net is not None
    }

    return jsonify(response)


@accounting_api.route("/net", methods=["POST", "PUT"])  # /api/v1/accounting/net
@limiter.limit("30 per minute, 200 per hour")  # Rate limiting for data modification
@require_csrf
@login_required
def save_daily_net():
    """Save daily Net calculation to database"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Missing request body"}), 400

        date_str = data.get("date")
        if not date_str:
            return jsonify({"success": False, "error": "Missing required 'date' field (YYYY-MM-DD)"}), 400

        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # Check if manual override for anlik_kasa_usd is requested
        anlik_kasa_manual = data.get("anlik_kasa_manual", False)
        confirmation_code = data.get("confirmation_code", "")
        
        # If manual override is requested, verify secret code
        if anlik_kasa_manual:
            from flask import current_app
            expected_code = current_app.config.get('BULK_DELETE_CONFIRMATION_CODE', '4561')
            if confirmation_code != expected_code:
                return jsonify({
                    "success": False,
                    "error": "Invalid confirmation code",
                    "message": "Please enter the correct 4-digit confirmation code to enable manual override"
                }), 400

        # Get or create DailyNet record
        query = DailyNet.query.filter_by(date=target_date)
        # Multi-tenancy: Apply organization filter
        query = add_tenant_filter(query, DailyNet)
        daily_net = query.first()
        
        if daily_net:
            # Update existing
            daily_net.net_cash_usd = _to_decimal(data.get("net_cash_usd", 0))
            daily_net.expenses_usd = _to_decimal(data.get("expenses_usd", 0))
            daily_net.commissions_usd = _to_decimal(data.get("commissions_usd", 0))
            daily_net.rollover_usd = _to_decimal(data.get("rollover_usd", 0))
            daily_net.net_saglama_usd = _to_decimal(data.get("net_saglama_usd", 0))
            daily_net.onceki_kapanis_usd = _to_decimal(data.get("onceki_kapanis_usd", 0))
            daily_net.company_cash_usd = _to_decimal(data.get("company_cash_usd", 0))
            daily_net.crypto_balance_usd = _to_decimal(data.get("crypto_balance_usd", 0))
            daily_net.anlik_kasa_usd = _to_decimal(data.get("anlik_kasa_usd", 0))
            daily_net.anlik_kasa_manual = anlik_kasa_manual
            daily_net.bekleyen_tahsilat_usd = _to_decimal(data.get("bekleyen_tahsilat_usd", 0))
            daily_net.fark_usd = _to_decimal(data.get("fark_usd", 0))
            daily_net.fark_bottom_usd = _to_decimal(data.get("fark_bottom_usd", 0))
            daily_net.notes = data.get("notes")
            daily_net.updated_at = datetime.now()
        else:
            # Create new
            daily_net = DailyNet(
                date=target_date,
                net_cash_usd=_to_decimal(data.get("net_cash_usd", 0)),
                expenses_usd=_to_decimal(data.get("expenses_usd", 0)),
                commissions_usd=_to_decimal(data.get("commissions_usd", 0)),
                rollover_usd=_to_decimal(data.get("rollover_usd", 0)),
                net_saglama_usd=_to_decimal(data.get("net_saglama_usd", 0)),
                onceki_kapanis_usd=_to_decimal(data.get("onceki_kapanis_usd", 0)),
                company_cash_usd=_to_decimal(data.get("company_cash_usd", 0)),
                crypto_balance_usd=_to_decimal(data.get("crypto_balance_usd", 0)),
                anlik_kasa_usd=_to_decimal(data.get("anlik_kasa_usd", 0)),
                anlik_kasa_manual=anlik_kasa_manual,
                bekleyen_tahsilat_usd=_to_decimal(data.get("bekleyen_tahsilat_usd", 0)),
                fark_usd=_to_decimal(data.get("fark_usd", 0)),
                fark_bottom_usd=_to_decimal(data.get("fark_bottom_usd", 0)),
                notes=data.get("notes"),
                created_by=current_user.id if current_user.is_authenticated else None
            )
            # Multi-tenancy: Set organization_id automatically
            set_tenant_on_new_record(daily_net)
            
            db.session.add(daily_net)

        db.session.commit()
        logger.info(f"Saved daily net for date {target_date}")

        return jsonify({
            "success": True,
            "message": "Daily net calculation saved successfully",
            "data": daily_net.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving daily net: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"Failed to save daily net: {str(e)}"}), 500


@accounting_api.route("/net/history", methods=["GET"])  # /api/v1/accounting/net/history
@login_required
def get_net_history():
    """Get all saved Net calculations, ordered by date descending"""
    try:
        # Optional date range filter
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        limit = request.args.get("limit", 30, type=int)  # Default to last 30 records
        
        query = DailyNet.query
        
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                query = query.filter(DailyNet.date >= start)
            except ValueError:
                pass
        
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                query = query.filter(DailyNet.date <= end)
            except ValueError:
                pass
        
        records = query.order_by(DailyNet.date.desc()).limit(limit).all()
        
        return jsonify({
            "success": True,
            "data": [record.to_dict() for record in records],
            "count": len(records)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching net history: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"Failed to fetch net history: {str(e)}"}), 500


@accounting_api.route("/net/<date>", methods=["DELETE"])  # /api/v1/accounting/net/YYYY-MM-DD
@limiter.limit("10 per minute, 50 per hour")  # Very strict rate limiting for deletions
@require_csrf
@login_required
def delete_daily_net(date):
    """Delete a saved Net calculation"""
    try:
        # Verify confirmation code
        data = request.get_json() or {}
        confirmation_code = data.get("confirmation_code", "")
        
        from flask import current_app
        expected_code = current_app.config.get('BULK_DELETE_CONFIRMATION_CODE', '4561')
        
        if confirmation_code != expected_code:
            return jsonify({
                "success": False,
                "error": "Invalid confirmation code",
                "message": "Please enter the correct 4-digit confirmation code to delete"
            }), 400
        
        # Parse date
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Find and delete record
        daily_net = DailyNet.query.filter_by(date=target_date).first()
        
        if not daily_net:
            return jsonify({"success": False, "error": "No record found for this date"}), 404
        
        db.session.delete(daily_net)
        db.session.commit()
        
        logger.info(f"Deleted daily net for date {target_date}")
        
        return jsonify({
            "success": True,
            "message": "Record deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting daily net: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"Failed to delete record: {str(e)}"}), 500


# ============================================================================
# BUDGET MANAGEMENT ENDPOINTS
# ============================================================================

@accounting_api.route("/budgets", methods=["GET"])  # /api/v1/accounting/budgets
@login_required
def get_budgets():
    """Get all budgets with optional filtering"""
    try:
        # Optional filters
        budget_period = request.args.get("budget_period")
        category = request.args.get("category")
        is_active = request.args.get("is_active")
        
        query = ExpenseBudget.query
        
        if budget_period:
            query = query.filter(ExpenseBudget.budget_period == budget_period)
        
        if category:
            if category == 'overall':
                query = query.filter(ExpenseBudget.category.is_(None))
            else:
                query = query.filter(ExpenseBudget.category == category)
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter(ExpenseBudget.is_active == is_active_bool)
        
        budgets = query.order_by(ExpenseBudget.budget_period.desc()).all()
        
        return jsonify({
            "success": True,
            "budgets": [budget.to_dict() for budget in budgets],
            "count": len(budgets)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching budgets: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "budgets": []
        }), 500


@accounting_api.route("/budgets/<int:budget_id>", methods=["GET"])  # /api/v1/accounting/budgets/<id>
@login_required
def get_budget(budget_id):
    """Get a specific budget by ID"""
    try:
        budget = ExpenseBudget.query.get_or_404(budget_id)
        return jsonify({
            "success": True,
            "budget": budget.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching budget {budget_id}: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@accounting_api.route("/budgets", methods=["POST"])  # /api/v1/accounting/budgets
@limiter.limit("30 per minute, 200 per hour")
@require_csrf
@login_required
def create_budget():
    """Create a new budget"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Missing request body"}), 400
        
        # Validate required fields
        if not data.get('budget_period'):
            return jsonify({"success": False, "error": "Budget period is required"}), 400
        
        # Check if budget already exists for this period/category combination
        category = data.get('category') if data.get('category') != 'overall' else None
        query = ExpenseBudget.query.filter_by(
            budget_period=data['budget_period'],
            category=category
        )
        # Multi-tenancy: Apply organization filter
        query = add_tenant_filter(query, ExpenseBudget)
        existing_budget = query.first()
        
        if existing_budget:
            return jsonify({
                "success": False,
                "error": "Budget already exists for this period and category"
            }), 400
        
        # Create budget
        budget = ExpenseBudget(
            budget_period=data['budget_period'],
            budget_type=data.get('budget_type', 'monthly'),
            category=category,
            budget_try=_to_decimal(data.get('budget_try', 0)),
            budget_usd=_to_decimal(data.get('budget_usd', 0)),
            budget_usdt=_to_decimal(data.get('budget_usdt', 0)),
            warning_threshold=data.get('warning_threshold', 80),
            alert_threshold=data.get('alert_threshold', 100),
            is_active=data.get('is_active', True),
            notes=data.get('notes', ''),
            created_by=current_user.id if current_user.is_authenticated else None
        )
        
        # Multi-tenancy: Set organization_id automatically
        set_tenant_on_new_record(budget)
        
        db.session.add(budget)
        db.session.commit()
        
        logger.info(f"Created budget {budget.id} by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
        
        return jsonify({
            "success": True,
            "message": "Budget created successfully",
            "budget": budget.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating budget: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to create budget: {str(e)}"
        }), 500


@accounting_api.route("/budgets/<int:budget_id>", methods=["PUT"])  # /api/v1/accounting/budgets/<id>
@limiter.limit("30 per minute, 200 per hour")
@require_csrf
@login_required
def update_budget(budget_id):
    """Update an existing budget"""
    try:
        budget = ExpenseBudget.query.get_or_404(budget_id)
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "Missing request body"}), 400
        
        # Update fields
        if 'budget_period' in data:
            budget.budget_period = data['budget_period']
        if 'budget_type' in data:
            budget.budget_type = data['budget_type']
        if 'category' in data:
            budget.category = data['category'] if data['category'] != 'overall' else None
        if 'budget_try' in data:
            budget.budget_try = _to_decimal(data['budget_try'])
        if 'budget_usd' in data:
            budget.budget_usd = _to_decimal(data['budget_usd'])
        if 'budget_usdt' in data:
            budget.budget_usdt = _to_decimal(data['budget_usdt'])
        if 'warning_threshold' in data:
            budget.warning_threshold = data['warning_threshold']
        if 'alert_threshold' in data:
            budget.alert_threshold = data['alert_threshold']
        if 'is_active' in data:
            budget.is_active = data['is_active']
        if 'notes' in data:
            budget.notes = data['notes']
        
        budget.updated_at = datetime.now()
        db.session.commit()
        
        logger.info(f"Updated budget {budget_id} by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
        
        return jsonify({
            "success": True,
            "message": "Budget updated successfully",
            "budget": budget.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating budget {budget_id}: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to update budget: {str(e)}"
        }), 500


@accounting_api.route("/budgets/<int:budget_id>", methods=["DELETE"])  # /api/v1/accounting/budgets/<id>
@limiter.limit("20 per minute, 100 per hour")
@require_csrf
@login_required
def delete_budget(budget_id):
    """Delete a budget"""
    try:
        budget = ExpenseBudget.query.get_or_404(budget_id)
        db.session.delete(budget)
        db.session.commit()
        
        logger.info(f"Deleted budget {budget_id} by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
        
        return jsonify({
            "success": True,
            "message": "Budget deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting budget {budget_id}: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to delete budget: {str(e)}"
        }), 500


# ============================================================================
# EXPENSE ANALYTICS ENDPOINTS
# ============================================================================

@accounting_api.route("/expenses/analytics", methods=["GET"])  # /api/v1/accounting/expenses/analytics
@login_required
def get_expense_analytics():
    """Get comprehensive expense analytics with trends, breakdowns, and summaries"""
    try:
        # Get date range from query params (default to last 6 months)
        end_date_str = request.args.get("end_date", datetime.now().strftime("%Y-%m-%d"))
        start_date_str = request.args.get("start_date")
        
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            end_date = datetime.now().date()
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                start_date = end_date - timedelta(days=180)
        else:
            start_date = end_date - timedelta(days=180)
        
        # Get currency for analytics (default: USD)
        currency = request.args.get("currency", "USD").upper()
        amount_field = f"amount_{currency.lower()}"
        
        # Query expenses in date range
        expenses = Expense.query.filter(
            Expense.payment_date.between(start_date, end_date)
        ).all()
        
        # Calculate summary statistics
        total_expenses = sum(getattr(exp, amount_field, 0) for exp in expenses)
        total_inflow = sum(getattr(exp, amount_field, 0) for exp in expenses if exp.category == 'inflow')
        total_outflow = sum(getattr(exp, amount_field, 0) for exp in expenses if exp.category == 'outflow')
        paid_count = sum(1 for exp in expenses if exp.status == 'paid')
        pending_count = sum(1 for exp in expenses if exp.status == 'pending')
        cancelled_count = sum(1 for exp in expenses if exp.status == 'cancelled')
        avg_expense = total_expenses / len(expenses) if expenses else 0
        
        # Monthly trend data (last 6 months)
        monthly_trends = {}
        current_month = start_date.replace(day=1)
        while current_month <= end_date:
            month_key = current_month.strftime("%Y-%m")
            next_month = (current_month + timedelta(days=32)).replace(day=1)
            
            month_expenses = [
                exp for exp in expenses 
                if exp.payment_date and current_month <= exp.payment_date < next_month
            ]
            
            monthly_trends[month_key] = {
                "month": month_key,
                "total": float(sum(getattr(exp, amount_field, 0) for exp in month_expenses)),
                "inflow": float(sum(getattr(exp, amount_field, 0) for exp in month_expenses if exp.category == 'inflow')),
                "outflow": float(sum(getattr(exp, amount_field, 0) for exp in month_expenses if exp.category == 'outflow')),
                "count": len(month_expenses)
            }
            
            current_month = next_month
        
        # Category breakdown
        category_breakdown = {
            "inflow": float(total_inflow),
            "outflow": float(total_outflow)
        }
        
        # Status breakdown
        status_breakdown = {
            "paid": paid_count,
            "pending": pending_count,
            "cancelled": cancelled_count
        }
        
        # Top expenses (by amount)
        top_expenses = sorted(
            [{"id": exp.id, "description": exp.description, "amount": float(getattr(exp, amount_field, 0)), "date": exp.payment_date.isoformat() if exp.payment_date else None} 
             for exp in expenses],
            key=lambda x: x["amount"],
            reverse=True
        )[:10]
        
        # Current month summary
        current_month_start = datetime.now().date().replace(day=1)
        next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)
        current_month_expenses = [
            exp for exp in expenses 
            if exp.payment_date and current_month_start <= exp.payment_date < next_month_start
        ]
        
        current_month_summary = {
            "total": float(sum(getattr(exp, amount_field, 0) for exp in current_month_expenses)),
            "inflow": float(sum(getattr(exp, amount_field, 0) for exp in current_month_expenses if exp.category == 'inflow')),
            "outflow": float(sum(getattr(exp, amount_field, 0) for exp in current_month_expenses if exp.category == 'outflow')),
            "count": len(current_month_expenses),
            "paid_count": sum(1 for exp in current_month_expenses if exp.status == 'paid'),
            "pending_count": sum(1 for exp in current_month_expenses if exp.status == 'pending')
        }
        
        return jsonify({
            "success": True,
            "data": {
                "summary": {
                    "total_expenses": float(total_expenses),
                    "total_inflow": float(total_inflow),
                    "total_outflow": float(total_outflow),
                    "net_amount": float(total_inflow - total_outflow),
                    "total_count": len(expenses),
                    "paid_count": paid_count,
                    "pending_count": pending_count,
                    "cancelled_count": cancelled_count,
                    "average_expense": float(avg_expense)
                },
                "monthly_trends": list(monthly_trends.values()),
                "category_breakdown": category_breakdown,
                "status_breakdown": status_breakdown,
                "top_expenses": top_expenses,
                "current_month": current_month_summary,
                "date_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "currency": currency
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching expense analytics: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@accounting_api.route("/budgets/status", methods=["GET"])  # /api/v1/accounting/budgets/status
@login_required
def get_budget_status():
    """Get budget status with current spending vs budget comparison"""
    try:
        # Get budget period (default to current month)
        budget_period = request.args.get("budget_period", datetime.now().strftime("%Y-%m"))
        currency = request.args.get("currency", "USD").upper()
        amount_field = f"amount_{currency.lower()}"
        budget_field = f"budget_{currency.lower()}"
        
        # Get active budgets for the period
        budgets = ExpenseBudget.query.filter_by(
            budget_period=budget_period,
            is_active=True
        ).all()
        
        if not budgets:
            return jsonify({
                "success": True,
                "data": {
                    "budget_period": budget_period,
                    "currency": currency,
                    "budgets": [],
                    "has_budgets": False
                }
            }), 200
        
        # Parse budget period to get date range
        try:
            year, month = map(int, budget_period.split('-'))
            period_start = datetime(year, month, 1).date()
            next_month = (period_start + timedelta(days=32)).replace(day=1)
            period_end = next_month - timedelta(days=1)
        except:
            return jsonify({"success": False, "error": "Invalid budget_period format. Use YYYY-MM"}), 400
        
        # Get expenses for this period
        expenses = Expense.query.filter(
            Expense.payment_date.between(period_start, period_end)
        ).all()
        
        budget_status_list = []
        
        for budget in budgets:
            budget_amount = float(getattr(budget, budget_field, 0))
            
            # Filter expenses by category if budget has category
            if budget.category:
                category_expenses = [exp for exp in expenses if exp.category == budget.category]
            else:
                category_expenses = expenses
            
            # Calculate actual spending
            actual_amount = float(sum(getattr(exp, amount_field, 0) for exp in category_expenses))
            
            # Calculate percentages
            usage_percentage = (actual_amount / budget_amount * 100) if budget_amount > 0 else 0
            remaining_amount = budget_amount - actual_amount
            remaining_percentage = 100 - usage_percentage
            
            # Determine status
            if usage_percentage >= budget.alert_threshold:
                status = "alert"
            elif usage_percentage >= budget.warning_threshold:
                status = "warning"
            else:
                status = "good"
            
            budget_status_list.append({
                "budget_id": budget.id,
                "category": budget.category or "overall",
                "budget_amount": budget_amount,
                "actual_amount": actual_amount,
                "remaining_amount": remaining_amount,
                "usage_percentage": round(usage_percentage, 2),
                "remaining_percentage": round(remaining_percentage, 2),
                "status": status,
                "warning_threshold": budget.warning_threshold,
                "alert_threshold": budget.alert_threshold,
                "expense_count": len(category_expenses)
            })
        
        return jsonify({
            "success": True,
            "data": {
                "budget_period": budget_period,
                "currency": currency,
                "budgets": budget_status_list,
                "has_budgets": True,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching budget status: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# MONTHLY CURRENCY SUMMARY ENDPOINTS (Internal Revenue)
# ============================================================================

@accounting_api.route("/currency-summary/<month_period>", methods=["GET"])  # /api/v1/accounting/currency-summary/2025-01
@login_required
def get_monthly_currency_summary(month_period):
    """Get currency summary for a specific month"""
    try:
        # Validate month_period format (YYYY-MM)
        try:
            datetime.strptime(month_period, "%Y-%m")
        except ValueError:
            return jsonify({"success": False, "error": "Invalid month format. Use YYYY-MM"}), 400
        
        # Get saved data for this month
        summaries = MonthlyCurrencySummary.query.filter_by(month_period=month_period).all()
        
        if summaries:
            # Return saved data
            return jsonify({
                "success": True,
                "month_period": month_period,
                "is_saved": True,
                "is_locked": summaries[0].is_locked if summaries else False,
                "currencies": [summary.to_dict() for summary in summaries]
            }), 200
        else:
            # No saved data, return empty
            return jsonify({
                "success": True,
                "month_period": month_period,
                "is_saved": False,
                "is_locked": False,
                "currencies": []
            }), 200
            
    except Exception as e:
        logger.error(f"Error fetching monthly currency summary: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@accounting_api.route("/currency-summary", methods=["POST"])  # /api/v1/accounting/currency-summary
@limiter.limit("30 per minute, 200 per hour")
@require_csrf
@login_required
def save_monthly_currency_summary():
    """Save currency summary for a month"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Missing request body"}), 400
        
        month_period = data.get('month_period')
        if not month_period:
            return jsonify({"success": False, "error": "month_period is required"}), 400
        
        # Validate month_period format
        try:
            datetime.strptime(month_period, "%Y-%m")
        except ValueError:
            return jsonify({"success": False, "error": "Invalid month format. Use YYYY-MM"}), 400
        
        currencies_data = data.get('currencies', [])
        if not currencies_data:
            return jsonify({"success": False, "error": "currencies data is required"}), 400
        
        # Check if month is locked
        query = MonthlyCurrencySummary.query.filter_by(month_period=month_period)
        # Multi-tenancy: Apply organization filter
        query = add_tenant_filter(query, MonthlyCurrencySummary)
        existing = query.first()
        
        if existing and existing.is_locked:
            return jsonify({
                "success": False,
                "error": "This month is locked and cannot be modified"
            }), 400
        
        saved_summaries = []
        
        for currency_data in currencies_data:
            currency = currency_data.get('currency')
            if not currency or currency not in ['TRY', 'USD', 'USDT']:
                continue
            
            # Get or create summary for this currency
            query = MonthlyCurrencySummary.query.filter_by(
                month_period=month_period,
                currency=currency
            )
            # Multi-tenancy: Apply organization filter
            query = add_tenant_filter(query, MonthlyCurrencySummary)
            summary = query.first()
            
            if not summary:
                summary = MonthlyCurrencySummary(
                    month_period=month_period,
                    currency=currency,
                    created_by=current_user.id if current_user.is_authenticated else None
                )
                # Multi-tenancy: Set organization_id automatically
                set_tenant_on_new_record(summary)
                db.session.add(summary)
            
            # Update fields
            summary.devir = _to_decimal(currency_data.get('devir', 0))
            summary.exchange_rate = _to_decimal(currency_data.get('exchange_rate')) if currency_data.get('exchange_rate') else None
            summary.inflow = _to_decimal(currency_data.get('inflow', 0))
            summary.outflow = _to_decimal(currency_data.get('outflow', 0))
            summary.net = _to_decimal(currency_data.get('net', 0))
            summary.usd_equivalent = _to_decimal(currency_data.get('usd_equivalent', 0))
            summary.notes = currency_data.get('notes', '')
            summary.updated_at = datetime.now()
            
            saved_summaries.append(summary)
        
        db.session.commit()
        
        logger.info(f"Saved currency summary for {month_period} by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
        
        return jsonify({
            "success": True,
            "message": "Currency summary saved successfully",
            "month_period": month_period,
            "currencies": [s.to_dict() for s in saved_summaries]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving monthly currency summary: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to save currency summary: {str(e)}"
        }), 500


@accounting_api.route("/currency-summary/<month_period>/lock", methods=["POST"])  # /api/v1/accounting/currency-summary/2025-01/lock
@limiter.limit("20 per minute, 100 per hour")
@require_csrf
@login_required
def lock_monthly_currency_summary(month_period):
    """Lock a month to prevent further modifications"""
    try:
        # Validate month_period format
        try:
            datetime.strptime(month_period, "%Y-%m")
        except ValueError:
            return jsonify({"success": False, "error": "Invalid month format. Use YYYY-MM"}), 400
        
        # Get all summaries for this month
        summaries = MonthlyCurrencySummary.query.filter_by(month_period=month_period).all()
        
        if not summaries:
            return jsonify({
                "success": False,
                "error": "No data found for this month. Save data first before locking."
            }), 404
        
        # Lock all summaries for this month
        for summary in summaries:
            summary.is_locked = True
            summary.updated_at = datetime.now()
        
        db.session.commit()
        
        logger.info(f"Locked currency summary for {month_period} by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
        
        return jsonify({
            "success": True,
            "message": f"Month {month_period} locked successfully",
            "month_period": month_period
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error locking monthly currency summary: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to lock month: {str(e)}"
        }), 500


@accounting_api.route("/currency-summary/<month_period>/unlock", methods=["POST"])  # /api/v1/accounting/currency-summary/2025-01/unlock
@limiter.limit("20 per minute, 100 per hour")
@require_csrf
@login_required
def unlock_monthly_currency_summary(month_period):
    """Unlock a month to allow modifications"""
    try:
        # Validate month_period format
        try:
            datetime.strptime(month_period, "%Y-%m")
        except ValueError:
            return jsonify({"success": False, "error": "Invalid month format. Use YYYY-MM"}), 400
        
        # Get all summaries for this month
        summaries = MonthlyCurrencySummary.query.filter_by(month_period=month_period).all()
        
        if not summaries:
            return jsonify({
                "success": False,
                "error": "No data found for this month"
            }), 404
        
        # Unlock all summaries for this month
        for summary in summaries:
            summary.is_locked = False
            summary.updated_at = datetime.now()
        
        db.session.commit()
        
        logger.info(f"Unlocked currency summary for {month_period} by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
        
        return jsonify({
            "success": True,
            "message": f"Month {month_period} unlocked successfully",
            "month_period": month_period
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error unlocking monthly currency summary: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Failed to unlock month: {str(e)}"
        }), 500


@accounting_api.route("/currency-summary/months", methods=["GET"])  # /api/v1/accounting/currency-summary/months
@login_required
def get_saved_months():
    """Get list of months that have saved currency summaries"""
    try:
        # Get distinct month periods
        months = db.session.query(
            MonthlyCurrencySummary.month_period,
            MonthlyCurrencySummary.is_locked
        ).distinct().order_by(MonthlyCurrencySummary.month_period.desc()).all()
        
        month_list = [
            {
                "month_period": month[0],
                "is_locked": month[1]
            }
            for month in months
        ]
        
        return jsonify({
            "success": True,
            "months": month_list,
            "count": len(month_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching saved months: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


