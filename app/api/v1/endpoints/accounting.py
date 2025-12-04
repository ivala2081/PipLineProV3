"""
Accounting API endpoints
Provides daily Net calculation used by the Accounting → Net tab
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func
from datetime import datetime
from decimal import Decimal
import logging

from app import db
from app.models.transaction import Transaction
from app.models.financial import DailyNet
from flask_login import current_user

logger = logging.getLogger(__name__)

accounting_api = Blueprint('accounting_api', __name__)

# Temporarily disable CSRF protection for this API (non-production only)
from app import csrf
csrf.exempt(accounting_api)


@accounting_api.route("/expenses", methods=["GET"])  # /api/v1/accounting/expenses
@login_required
def get_expenses():
    """Get all expenses - placeholder endpoint until Expense model is implemented"""
    try:
        # TODO: Implement Expense model and database table
        # For now, return empty array to prevent frontend errors
        return jsonify({
            "success": True,
            "expenses": [],
            "message": "Expense tracking feature coming soon"
        })
    except Exception as e:
        logger.error(f"Error in get_expenses: {str(e)}")
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
        daily_net = DailyNet.query.filter_by(date=target_date).first()
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


