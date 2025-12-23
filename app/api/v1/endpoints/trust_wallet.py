"""
Trust Wallet API endpoints
Handles wallet management and transaction operations
"""
import logging
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc, asc
from sqlalchemy.exc import IntegrityError

from app import db, csrf
from app.models.trust_wallet import TrustWallet, TrustWalletTransaction
from app.services.trust_wallet_service import TrustWalletService
from app.utils.tenant_helpers import set_tenant_on_new_record, add_tenant_filter, validate_tenant_access

logger = logging.getLogger(__name__)

# Create Blueprint
trust_wallet_bp = Blueprint('trust_wallet', __name__)

# Exempt the entire blueprint from CSRF protection
# Trust wallet operations use token-based auth which is secure
csrf.exempt(trust_wallet_bp)

# Initialize service
trust_wallet_service = TrustWalletService()

@trust_wallet_bp.route('/wallets', methods=['GET'])
@login_required
def get_wallets():
    """Get all Trust wallets"""
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        wallets = trust_wallet_service.get_all_wallets(active_only=active_only)
        
        return jsonify({
            'success': True,
            'wallets': [wallet.to_dict() for wallet in wallets],
            'total_count': len(wallets)
        })
        
    except Exception as e:
        logger.error(f"Error getting wallets: {e}")
        return jsonify({'error': str(e)}), 500

@trust_wallet_bp.route('/wallets', methods=['POST'])
@login_required
def create_wallet():
    """Create a new Trust wallet"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['wallet_address', 'wallet_name', 'network']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f"Missing required field: {field}"}), 400
        
        # Get current user
        current_user_id = current_user.id
        
        # Create wallet
        wallet = trust_wallet_service.create_wallet(
            wallet_address=data['wallet_address'],
            wallet_name=data['wallet_name'],
            network=data['network'].upper(),
            created_by=current_user_id
        )
        
        return jsonify({
            'success': True,
            'wallet': wallet.to_dict(),
            'message': 'Wallet created successfully'
        }), 201
        
    except ValueError as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            return jsonify({'error': "This wallet address is already registered. Please use a different address."}), 409
        elif "Invalid" in error_msg:
            return jsonify({'error': "Invalid wallet address format. Please check the address and try again."}), 400
        else:
            return jsonify({'error': error_msg}), 400
    except IntegrityError as e:
        return jsonify({'error': "This wallet address is already registered. Please use a different address."}), 409
    except Exception as e:
        logger.error(f"Error creating wallet: {e}")
        return jsonify({'error': "Internal server error. Please try again."}), 500

@trust_wallet_bp.route('/wallets/<int:wallet_id>', methods=['GET'])
@login_required
def get_wallet(wallet_id):
    """Get a specific wallet"""
    try:
        wallet = trust_wallet_service.get_wallet_by_id(wallet_id)
        if not wallet:
            return jsonify({'error': "Wallet not found"}), 404
        
        return jsonify({
            'success': True,
            'wallet': wallet.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting wallet {wallet_id}: {e}")
        return jsonify({'error': str(e)}), 500

@trust_wallet_bp.route('/wallets/<int:wallet_id>', methods=['PUT'])
@login_required
def update_wallet(wallet_id):
    """Update wallet information"""
    try:
        data = request.get_json()
        
        wallet = trust_wallet_service.update_wallet(
            wallet_id=wallet_id,
            wallet_name=data.get('wallet_name'),
            is_active=data.get('is_active')
        )
        
        return jsonify({
            'success': True,
            'wallet': wallet.to_dict(),
            'message': 'Wallet updated successfully'
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating wallet {wallet_id}: {e}")
        return jsonify({'error': str(e)}), 500

@trust_wallet_bp.route('/wallets/<int:wallet_id>', methods=['DELETE'])
@login_required
def delete_wallet(wallet_id):
    """Delete a wallet"""
    try:
        success = trust_wallet_service.delete_wallet(wallet_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Wallet deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete wallet'}), 500
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            return jsonify({'error': 'Wallet not found'}), 404
        else:
            return jsonify({'error': error_msg}), 400
    except Exception as e:
        logger.error(f"Error deleting wallet {wallet_id}: {e}")
        return jsonify({'error': 'Internal server error. Please try again.'}), 500

@trust_wallet_bp.route('/wallets/<int:wallet_id>/transactions', methods=['GET'])
@login_required
def get_wallet_transactions(wallet_id):
    """Get token transfers for a specific wallet (TRC20/ERC20/BEP20 only)"""
    try:
        # Parse query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)  # Max 100 per page
        
        # Date filters
        start_date = None
        end_date = None
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date').replace('Z', '+00:00'))
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date').replace('Z', '+00:00'))
        
        # Other filters
        token_symbol = request.args.get('token_symbol')
        transaction_type = request.args.get('transaction_type')
        
        result = trust_wallet_service.get_wallet_transactions(
            wallet_id=wallet_id,
            page=page,
            per_page=per_page,
            start_date=start_date,
            end_date=end_date,
            token_symbol=token_symbol,
            transaction_type=transaction_type
        )
        
        return jsonify({
            'success': True,
            **result
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting wallet transactions {wallet_id}: {e}")
        return jsonify({'error': str(e)}), 500

@trust_wallet_bp.route('/wallets/<int:wallet_id>/summary', methods=['GET'])
@login_required
def get_wallet_summary(wallet_id):
    """Get summary statistics for a wallet"""
    try:
        # Date filters
        start_date = None
        end_date = None
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date').replace('Z', '+00:00'))
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date').replace('Z', '+00:00'))
        
        summary = trust_wallet_service.get_wallet_summary(
            wallet_id=wallet_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            'success': True,
            **summary
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting wallet summary {wallet_id}: {e}")
        return jsonify({'error': str(e)}), 500

@trust_wallet_bp.route('/wallets/<int:wallet_id>/sync', methods=['POST'])
@login_required
def sync_wallet(wallet_id):
    """Sync transactions for a specific wallet"""
    try:
        # Handle optional JSON body
        data = request.get_json(silent=True) or {}
        force_full_sync = data.get('force_full_sync', False)
        
        result = trust_wallet_service.sync_wallet_transactions(
            wallet_id=wallet_id,
            force_full_sync=force_full_sync
        )
        
        return jsonify({
            'success': True,
            'sync_result': result,
            'message': 'Wallet sync completed successfully'
        })
        
    except ValueError as e:
        error_msg = str(e)
        status_code = 400
        if "not found" in error_msg.lower():
            status_code = 404
        elif "not active" in error_msg.lower():
            status_code = 403
        
        logger.warning(f"Validation error syncing wallet {wallet_id}: {error_msg}")
        return jsonify({'error': error_msg, 'error_type': 'validation'}), status_code
        
    except Exception as e:
        logger.error(f"Error syncing wallet {wallet_id}: {e}", exc_info=True)
        
        # Return user-friendly error message with details for debugging
        error_msg = "Failed to sync wallet. Please try again later."
        error_details = str(e)
        
        # Check for specific error types
        if "database" in str(e).lower() or "sql" in str(e).lower():
            error_msg = "Database error occurred. Please contact support."
        elif "timeout" in str(e).lower():
            error_msg = "Sync request timed out. Please try again."
        elif "api" in str(e).lower() or "request" in str(e).lower():
            error_msg = f"Blockchain API error: {error_details}"
        
        return jsonify({
            'error': error_msg,
            'error_type': 'server_error',
            'details': error_details  # Always include details for debugging
        }), 500

@trust_wallet_bp.route('/wallets/sync-all', methods=['POST'])
@login_required
def sync_all_wallets():
    """Sync all active wallets"""
    try:
        data = request.get_json() or {}
        force_full_sync = data.get('force_full_sync', False)
        
        result = trust_wallet_service.sync_all_wallets(force_full_sync=force_full_sync)
        
        return jsonify({
            'success': True,
            'sync_result': result,
            'message': 'All wallets sync completed'
        })
        
    except Exception as e:
        logger.error(f"Error syncing all wallets: {e}")
        return jsonify({'error': str(e)}), 500

@trust_wallet_bp.route('/transactions', methods=['GET'])
@login_required
def get_all_transactions():
    """Get token transfers from all wallets (TRC20/ERC20/BEP20 only, excluding native token transactions)"""
    try:
        # Parse query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        
        # Date filters
        start_date = None
        end_date = None
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date').replace('Z', '+00:00'))
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date').replace('Z', '+00:00'))
        
        # Other filters
        wallet_id = request.args.get('wallet_id')
        network = request.args.get('network')
        token_symbol = request.args.get('token_symbol')
        transaction_type = request.args.get('transaction_type')
        
        # Build query
        query = TrustWalletTransaction.query.join(TrustWallet)
        
        if start_date:
            query = query.filter(TrustWalletTransaction.block_timestamp >= start_date)
        if end_date:
            query = query.filter(TrustWalletTransaction.block_timestamp <= end_date)
        if wallet_id:
            query = query.filter(TrustWalletTransaction.wallet_id == wallet_id)
        if network:
            query = query.filter(TrustWalletTransaction.network == network.upper())
        if token_symbol:
            query = query.filter(TrustWalletTransaction.token_symbol == token_symbol)
        if transaction_type:
            query = query.filter(TrustWalletTransaction.transaction_type == transaction_type.upper())
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        transactions = query.order_by(desc(TrustWalletTransaction.block_timestamp))\
                          .offset((page - 1) * per_page)\
                          .limit(per_page)\
                          .all()
        
        return jsonify({
            'success': True,
            'transactions': [tx.to_dict() for tx in transactions],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting all transactions: {e}")
        return jsonify({'error': str(e)}), 500

@trust_wallet_bp.route('/summary', methods=['GET'])
@login_required
def get_all_summary():
    """Get summary statistics for all wallets"""
    try:
        # Date filters
        start_date = None
        end_date = None
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date').replace('Z', '+00:00'))
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date').replace('Z', '+00:00'))
        
        summary = trust_wallet_service.get_all_transactions_summary(
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            'success': True,
            **summary
        })
        
    except Exception as e:
        logger.error(f"Error getting all summary: {e}")
        return jsonify({'error': str(e)}), 500

@trust_wallet_bp.route('/networks', methods=['GET'])
@login_required
def get_supported_networks():
    """Get list of supported blockchain networks"""
    try:
        networks = [
            {
                'code': 'ETH',
                'name': 'Ethereum',
                'description': 'Ethereum Mainnet',
                'native_token': 'ETH',
                'explorer_url': 'https://etherscan.io'
            },
            {
                'code': 'BSC',
                'name': 'Binance Smart Chain',
                'description': 'BSC Mainnet',
                'native_token': 'BNB',
                'explorer_url': 'https://bscscan.com'
            },
            {
                'code': 'TRC',
                'name': 'TRON',
                'description': 'TRON Mainnet',
                'native_token': 'TRX',
                'explorer_url': 'https://tronscan.org'
            }
        ]
        
        return jsonify({
            'success': True,
            'networks': networks
        })
        
    except Exception as e:
        logger.error(f"Error getting supported networks: {e}")
        return jsonify({'error': str(e)}), 500

@trust_wallet_bp.route('/tokens', methods=['GET'])
@login_required
def get_supported_tokens():
    """Get list of supported tokens by network"""
    try:
        tokens = {
            'ETH': [
                {'symbol': 'ETH', 'name': 'Ethereum', 'decimals': 18, 'contract_address': None},
                {'symbol': 'USDT', 'name': 'Tether USD', 'decimals': 6, 'contract_address': '0xdAC17F958D2ee523a2206206994597C13D831ec7'},
                {'symbol': 'USDC', 'name': 'USD Coin', 'decimals': 6, 'contract_address': '0xA0b86a33E6441b8C4C8C0E1234567890abcdef12'},
                {'symbol': 'DAI', 'name': 'Dai Stablecoin', 'decimals': 18, 'contract_address': '0x6B175474E89094C44Da98b954EedeAC495271d0F'},
            ],
            'BSC': [
                {'symbol': 'BNB', 'name': 'Binance Coin', 'decimals': 18, 'contract_address': None},
                {'symbol': 'USDT', 'name': 'Tether USD', 'decimals': 18, 'contract_address': '0x55d398326f99059fF775485246999027B3197955'},
                {'symbol': 'USDC', 'name': 'USD Coin', 'decimals': 18, 'contract_address': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d'},
                {'symbol': 'BUSD', 'name': 'Binance USD', 'decimals': 18, 'contract_address': '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56'},
            ],
            'TRC': [
                {'symbol': 'TRX', 'name': 'TRON', 'decimals': 6, 'contract_address': None},
                {'symbol': 'USDT', 'name': 'Tether USD', 'decimals': 6, 'contract_address': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'},
                {'symbol': 'USDC', 'name': 'USD Coin', 'decimals': 6, 'contract_address': 'TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8'},
            ]
        }
        
        return jsonify({
            'success': True,
            'tokens': tokens
        })
        
    except Exception as e:
        logger.error(f"Error getting supported tokens: {e}")
        return jsonify({'error': str(e)}), 500

@trust_wallet_bp.route('/wallets/<int:wallet_id>/balance', methods=['GET'])
@login_required
def get_wallet_balance(wallet_id: int):
    """Get wallet balance"""
    try:
        service = TrustWalletService()
        balance_data = service.get_wallet_balance(wallet_id)
        
        return jsonify({
            'success': True,
            'data': balance_data
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting wallet balance: {e}")
        return jsonify({'error': "Internal server error. Please try again."}), 500

@trust_wallet_bp.route('/wallets/<int:wallet_id>/historical-balances', methods=['GET'])
@login_required
def get_wallet_historical_balances(wallet_id: int):
    """Get historical daily balances for a wallet"""
    try:
        # Check if wallet exists
        wallet = TrustWallet.query.get(wallet_id)
        if not wallet:
            return jsonify({'error': 'Wallet not found'}), 404
        
        # Get date range from query parameters
        start_date = None
        end_date = None
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date').replace('Z', '+00:00')).date()
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date').replace('Z', '+00:00')).date()
        
        # If no date range provided, fetch from wallet birth (first transaction or creation date)
        if not start_date:
            # Try to get the earliest transaction date for this wallet
            earliest_tx = TrustWalletTransaction.query.filter(
                TrustWalletTransaction.wallet_id == wallet_id
            ).order_by(TrustWalletTransaction.block_timestamp.asc()).first()
            
            if earliest_tx:
                # Start from the date of the first transaction
                start_date = earliest_tx.block_timestamp.date()
                logger.info(f"Using wallet's first transaction date as start: {start_date}")
            else:
                # If no transactions, use wallet creation date
                start_date = wallet.created_at.date() if wallet.created_at else datetime.now(timezone.utc).date()
                logger.info(f"Using wallet creation date as start: {start_date}")
        
        if not end_date:
            end_date = datetime.now(timezone.utc).date()
        
        # Get all transactions for this wallet up to end_date
        query = TrustWalletTransaction.query.filter(
            TrustWalletTransaction.wallet_id == wallet_id,
            TrustWalletTransaction.block_timestamp <= datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        ).order_by(TrustWalletTransaction.block_timestamp)
        
        transactions = query.all()
        
        # Calculate daily balances
        from collections import defaultdict
        from decimal import Decimal
        
        # Dictionary to store daily balances: {date: {token: balance}}
        daily_balances = defaultdict(lambda: defaultdict(Decimal))
        
        # Calculate initial balance (before start_date)
        initial_balances = defaultdict(Decimal)
        
        # Process transactions chronologically
        for tx in transactions:
            tx_date = tx.block_timestamp.date()
            token = tx.token_symbol
            
            # Update balance based on transaction type
            if tx.transaction_type == 'IN':
                # Incoming transaction increases balance
                if tx_date < start_date:
                    initial_balances[token] += Decimal(str(tx.token_amount))
                else:
                    daily_balances[tx_date][token] += Decimal(str(tx.token_amount))
            elif tx.transaction_type == 'OUT':
                # Outgoing transaction decreases balance
                if tx_date < start_date:
                    initial_balances[token] -= Decimal(str(tx.token_amount))
                else:
                    daily_balances[tx_date][token] -= Decimal(str(tx.token_amount))
            # INTERNAL transactions don't change the wallet's balance
            
            # Also account for gas fees if paid from this wallet
            if tx.gas_fee and tx.gas_fee > 0:
                gas_token = tx.gas_fee_token
                # Gas is always deducted (OUT)
                if tx_date < start_date:
                    initial_balances[gas_token] -= Decimal(str(tx.gas_fee))
                else:
                    daily_balances[tx_date][gas_token] -= Decimal(str(tx.gas_fee))
        
        # Calculate cumulative balances per day - FIXED TO INCLUDE ALL DAYS
        all_tokens = set()
        
        # Collect all tokens from both initial and daily balances
        all_tokens.update(initial_balances.keys())
        for date_balances in daily_balances.values():
            all_tokens.update(date_balances.keys())
        
        # Start with initial balances
        current_balances = initial_balances.copy()
        
        # Generate ALL dates from start_date to end_date (not just transaction days)
        from datetime import timedelta
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            all_dates.append(current_date)
            current_date += timedelta(days=1)
        
        logger.info(f"Calculating historical balances for {len(all_dates)} days from {start_date} to {end_date}")
        logger.info(f"Found {len(transactions)} transactions across {len(daily_balances)} days with activity")
        
        # Format response with balances for EVERY day
        service = TrustWalletService()
        result = []
        
        for date in all_dates:
            # If there were transactions on this date, apply the changes
            if date in daily_balances:
                for token, change in daily_balances[date].items():
                    current_balances[token] += change
            
            # Build the response for this day (only include tokens with non-zero balances)
            day_balances = {}
            total_usd = Decimal('0')
            
            for token in all_tokens:
                balance = current_balances.get(token, Decimal('0'))
                
                # Skip tokens with zero or near-zero balance
                if abs(balance) < Decimal('0.000001'):
                    continue
                
                # Get USD value using service method
                try:
                    balance_float = float(balance)
                    usd_value = service._get_token_usd_value(token, balance_float)
                    total_usd += Decimal(str(usd_value))
                except Exception as e:
                    logger.warning(f"Error getting USD value for {token} on {date}: {e}")
                    usd_value = 0.0
                
                day_balances[token] = {
                    'amount': float(balance),
                    'usd_value': float(usd_value)
                }
            
            # Only add days with non-zero balances
            if day_balances:
                result.append({
                    'date': date.isoformat(),
                    'balances': day_balances,
                    'total_usd': float(total_usd)
                })
        
        return jsonify({
            'success': True,
            'wallet_id': wallet_id,
            'wallet_name': wallet.wallet_name,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'historical_balances': result
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting historical balances for wallet {wallet_id}: {e}", exc_info=True)
        return jsonify({'error': "Internal server error. Please try again."}), 500