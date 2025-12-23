"""
Trust Wallet service for managing blockchain transactions
Handles wallet management, transaction syncing, and data processing
"""
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import Session

from app import db
from app.models.trust_wallet import TrustWallet, TrustWalletTransaction
from app.services.blockchain_api_service import BlockchainAPIService, BlockchainTransaction
# Use enhanced exchange rate service (legacy service deprecated)
from app.services.enhanced_exchange_rate_service import EnhancedExchangeRateService as ExchangeRateService
from app.utils.tenant_helpers import set_tenant_on_new_record, add_tenant_filter

logger = logging.getLogger(__name__)

class TrustWalletService:
    """Service for managing Trust wallet operations"""
    
    def __init__(self):
        self.blockchain_api = BlockchainAPIService()
        self.exchange_service = ExchangeRateService()
    
    def create_wallet(self, wallet_address: str, wallet_name: str, network: str, created_by: int) -> TrustWallet:
        """Create a new Trust wallet"""
        try:
            # Check if wallet already exists (within current organization)
            query = TrustWallet.query.filter_by(wallet_address=wallet_address)
            query = add_tenant_filter(query, TrustWallet)
            existing_wallet = query.first()
            if existing_wallet:
                raise ValueError(f"Wallet address {wallet_address} already exists")
            
            wallet = TrustWallet(
                wallet_address=wallet_address,
                wallet_name=wallet_name,
                network=network,
                created_by=created_by,
                is_active=True
            )
            
            # Multi-tenancy: Set organization_id automatically
            set_tenant_on_new_record(wallet)
            
            db.session.add(wallet)
            db.session.commit()
            
            logger.info(f"Created Trust wallet: {wallet_name} ({network})")
            return wallet
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating wallet: {e}")
            raise
    
    def update_wallet(self, wallet_id: int, wallet_name: str = None, is_active: bool = None) -> TrustWallet:
        """Update wallet information"""
        try:
            wallet = TrustWallet.query.get(wallet_id)
            if not wallet:
                raise ValueError(f"Wallet with ID {wallet_id} not found")
            
            if wallet_name is not None:
                wallet.wallet_name = wallet_name
            if is_active is not None:
                wallet.is_active = is_active
            
            wallet.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"Updated wallet: {wallet.wallet_name}")
            return wallet
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating wallet: {e}")
            raise
    
    def delete_wallet(self, wallet_id: int) -> bool:
        """Delete a wallet and all its transactions"""
        try:
            wallet = TrustWallet.query.get(wallet_id)
            if not wallet:
                raise ValueError(f"Wallet with ID {wallet_id} not found")
            
            wallet_name = wallet.wallet_name  # Store name before deletion
            
            # Delete the wallet (cascade will handle transactions automatically)
            db.session.delete(wallet)
            db.session.commit()
            
            logger.info(f"Deleted wallet: {wallet_name}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting wallet: {e}")
            raise
    
    def get_all_wallets(self, active_only: bool = True) -> List[TrustWallet]:
        """Get all wallets"""
        query = TrustWallet.query
        # Multi-tenancy: Apply organization filter
        query = add_tenant_filter(query, TrustWallet)
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.order_by(TrustWallet.created_at.desc()).all()
    
    def get_wallet_by_id(self, wallet_id: int) -> Optional[TrustWallet]:
        """Get wallet by ID"""
        return TrustWallet.query.get(wallet_id)
    
    def sync_wallet_transactions(self, wallet_id: int, force_full_sync: bool = False) -> Dict:
        """Sync transactions for a specific wallet"""
        try:
            wallet = TrustWallet.query.get(wallet_id)
            if not wallet:
                raise ValueError(f"Wallet with ID {wallet_id} not found")
            
            if not wallet.is_active:
                raise ValueError(f"Wallet {wallet.wallet_name} is not active")
            
            logger.info(f"Starting sync for wallet: {wallet.wallet_name} ({wallet.network}), force_full_sync={force_full_sync}")
            
            # Determine start block - if force_full_sync, start from 0
            start_block = 0 if force_full_sync else (wallet.last_sync_block or 0)
            if force_full_sync:
                logger.info(f"Force full sync: resetting start_block to 0 to fetch all transactions")
            
            # Fetch real transactions from blockchain
            try:
                blockchain_txs = self.blockchain_api.get_wallet_transactions(
                    wallet_address=wallet.wallet_address,
                    network=wallet.network,
                    start_block=start_block,
                    end_block=None
                )
                logger.info(f"Fetched {len(blockchain_txs)} transactions from blockchain API (start_block={start_block})")
            except Exception as api_error:
                logger.error(f"Error fetching from blockchain API: {api_error}", exc_info=True)
                raise
            
            # Convert BlockchainTransaction objects to dict format
            sample_transactions = []
            for tx in blockchain_txs:
                sample_transactions.append({
                    'transaction_hash': tx.transaction_hash,
                    'block_number': tx.block_number,
                    'block_timestamp': tx.block_timestamp,
                    'from_address': tx.from_address,
                    'to_address': tx.to_address,
                    'token_symbol': tx.token_symbol,
                    'token_name': getattr(tx, 'token_name', None),
                    'token_address': tx.token_address,
                    'token_amount': tx.token_amount,
                    'token_decimals': tx.token_decimals,
                    'transaction_type': tx.transaction_type,
                    'gas_fee': tx.gas_fee,
                    'gas_fee_token': tx.gas_fee_token,
                    'status': tx.status,
                    'confirmations': tx.confirmations,
                    'network': tx.network
                })
            
            # Process and save TRANSFER transactions (token movements)
            # Using Tronscan API, we get transfers, not all transaction types
            # For TRC network, keep all transfers (including TRX transfers)
            # For ETH/BSC, keep token transfers and skip raw native token transactions
            transfer_transactions = []
            native_tokens = ['ETH', 'BNB', 'TRX']
            
            for sample_tx in sample_transactions:
                # For TRC network (Tronscan API), keep all transfers
                if sample_tx['network'] == 'TRC':
                    transfer_transactions.append(sample_tx)
                # For ETH/BSC, only keep token transfers (not raw native token transactions)
                elif sample_tx['token_symbol'] not in native_tokens or sample_tx.get('token_address'):
                    transfer_transactions.append(sample_tx)
                else:
                    logger.debug(f"Skipping native token transaction: {sample_tx['token_symbol']} - {sample_tx['transaction_hash'][:16]}...")
            
            logger.info(f"Filtered to {len(transfer_transactions)} transfer transactions out of {len(sample_transactions)} total")
            
            # Check for any orphaned transactions from before deletion
            orphaned_count = TrustWalletTransaction.query.filter(
                TrustWalletTransaction.transaction_hash.in_([tx.get('transaction_hash') for tx in transfer_transactions if tx.get('transaction_hash')])
            ).count()
            if orphaned_count > 0:
                logger.warning(f"Found {orphaned_count} orphaned transactions with matching hashes")
            
            new_transactions = 0
            updated_transactions = 0
            
            for idx, sample_tx in enumerate(transfer_transactions):
                # Check if transaction already exists
                tx_hash = sample_tx.get('transaction_hash', '')
                if not tx_hash:
                    logger.warning(f"Skipping transfer {idx} - missing transaction hash")
                    continue
                
                # Check for existing transaction with no_autoflush to prevent premature flush
                with db.session.no_autoflush:
                    existing_tx = TrustWalletTransaction.query.filter_by(
                        transaction_hash=tx_hash,
                        wallet_id=wallet.id
                    ).first()
                
                if existing_tx:
                    # Update existing transaction if needed
                    if idx < 3:
                        logger.info(f"Transaction {tx_hash[:16]}... already exists in DB for wallet {wallet.id}")
                    if existing_tx.confirmations < sample_tx['confirmations']:
                        existing_tx.confirmations = sample_tx['confirmations']
                        existing_tx.status = sample_tx['status']
                        existing_tx.updated_at = datetime.now(timezone.utc)
                        updated_transactions += 1
                else:
                    # Create new transaction
                    try:
                        if idx < 3:
                            logger.info(f"Creating new transaction {tx_hash[:16]}... with token {sample_tx['token_symbol']}")
                        db_tx = TrustWalletTransaction(
                            wallet_id=wallet.id,
                            transaction_hash=tx_hash,
                            block_number=sample_tx['block_number'],
                            block_timestamp=sample_tx['block_timestamp'],
                            from_address=sample_tx['from_address'],
                            to_address=sample_tx['to_address'],
                            token_symbol=sample_tx['token_symbol'],
                            token_name=sample_tx.get('token_name'),
                            token_address=sample_tx.get('token_address'),
                            token_amount=sample_tx['token_amount'],
                            token_decimals=sample_tx['token_decimals'],
                            transaction_type=sample_tx['transaction_type'],
                            gas_fee=sample_tx['gas_fee'],
                            gas_fee_token=sample_tx['gas_fee_token'],
                            status=sample_tx['status'],
                            confirmations=sample_tx['confirmations'],
                            network=sample_tx['network']
                        )
                        
                        db.session.add(db_tx)
                        new_transactions += 1
                        
                        if new_transactions <= 3:  # Log first 3
                            logger.info(f"Added transfer: {sample_tx['token_symbol']} {sample_tx['token_amount']} from {sample_tx['from_address'][:10]}...")
                    except Exception as e:
                        logger.error(f"Error creating transaction {idx}: {e}", exc_info=True)
                        logger.error(f"Transaction hash: {tx_hash}")
                        logger.error(f"Wallet ID: {wallet.id}")
                        # Check if it's a duplicate key error
                        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
                            logger.warning(f"Transaction {tx_hash[:16]}... already exists (unique constraint violation)")
                            # Try to get the existing transaction
                            existing_global = TrustWalletTransaction.query.filter_by(transaction_hash=tx_hash).first()
                            if existing_global:
                                logger.warning(f"Found existing transaction in different wallet: wallet_id={existing_global.wallet_id}")
                        continue
            
            # Update wallet sync information
            if sample_transactions:
                latest_block = max(tx['block_number'] for tx in sample_transactions)
                wallet.last_sync_block = latest_block
                wallet.last_sync_time = datetime.now(timezone.utc)
            
            # Flush to check for errors before commit
            committed_individually = False
            try:
                db.session.flush()
                logger.info(f"Successfully flushed {new_transactions} new transactions to database")
            except Exception as e:
                # Handle IntegrityError (duplicate transactions) gracefully
                from sqlalchemy.exc import IntegrityError
                if isinstance(e, IntegrityError) and 'unique' in str(e).lower():
                    logger.warning(f"IntegrityError during flush (likely duplicate transactions): {e}")
                    # Rollback and retry with individual transaction handling
                    db.session.rollback()
                    logger.info("Rolled back batch insert, will handle duplicates individually")
                    # Re-process transactions one by one to skip duplicates
                    for idx, sample_tx in enumerate(sample_transactions):
                        tx_hash = sample_tx.get('transaction_hash')
                        if not tx_hash:
                            continue
                        
                        existing_tx = TrustWalletTransaction.query.filter_by(
                            transaction_hash=tx_hash,
                            wallet_id=wallet.id
                        ).first()
                        
                        if not existing_tx:
                            try:
                                db_tx = TrustWalletTransaction(
                                    wallet_id=wallet.id,
                                    transaction_hash=tx_hash,
                                    block_number=sample_tx['block_number'],
                                    block_timestamp=sample_tx['block_timestamp'],
                                    from_address=sample_tx['from_address'],
                                    to_address=sample_tx['to_address'],
                                    token_symbol=sample_tx['token_symbol'],
                                    token_name=sample_tx.get('token_name'),
                                    token_address=sample_tx.get('token_address'),
                                    token_amount=sample_tx['token_amount'],
                                    token_decimals=sample_tx['token_decimals'],
                                    transaction_type=sample_tx['transaction_type'],
                                    gas_fee=sample_tx['gas_fee'],
                                    gas_fee_token=sample_tx['gas_fee_token'],
                                    status=sample_tx['status'],
                                    confirmations=sample_tx['confirmations'],
                                    network=sample_tx['network']
                                )
                                db.session.add(db_tx)
                                db.session.commit()
                                committed_individually = True
                            except IntegrityError:
                                db.session.rollback()
                                logger.debug(f"Skipping duplicate transaction {tx_hash[:16]}...")
                                continue
                else:
                    logger.error(f"Error during flush: {e}", exc_info=True)
                    db.session.rollback()
                    raise
            
            # Only commit if we didn't commit individually
            if not committed_individually:
                db.session.commit()
            
            result = {
                'wallet_id': wallet_id,
                'wallet_name': wallet.wallet_name,
                'network': wallet.network,
                'new_transactions': new_transactions,
                'updated_transactions': updated_transactions,
                'total_fetched': len(sample_transactions),
                'transfers_stored': len(transfer_transactions),
                'last_sync_block': wallet.last_sync_block,
                'last_sync_time': wallet.last_sync_time
            }
            
            logger.info(f"Sync completed for {wallet.wallet_name}: {new_transactions} new transfers, {updated_transactions} updated, {len(sample_transactions) - len(transfer_transactions)} native token txs skipped")
            return result
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error syncing wallet {wallet_id}: {e}")
            raise
    
    def _create_sample_transactions(self, wallet: TrustWallet) -> List[Dict]:
        """Create sample transactions for demonstration purposes"""
        import random
        from decimal import Decimal
        
        sample_transactions = []
        base_time = datetime.now(timezone.utc)
        
        # Create 5-8 sample transactions
        num_transactions = random.randint(5, 8)
        
        for i in range(num_transactions):
            # Generate random transaction hash
            tx_hash = f"0x{''.join(random.choices('0123456789abcdef', k=64))}"
            
            # Random transaction type
            tx_type = random.choice(['IN', 'OUT', 'INTERNAL'])
            
            # Random token
            token_names = {
                'ETH': 'Ethereum',
                'USDT': 'Tether USD',
                'USDC': 'USD Coin',
                'BNB': 'Binance Coin',
                'TRX': 'TRON'
            }
            
            if wallet.network == 'ETH':
                token_symbol = random.choice(['ETH', 'USDT', 'USDC'])
            elif wallet.network == 'BSC':
                token_symbol = random.choice(['BNB', 'USDT', 'USDC'])
            else:  # TRC
                token_symbol = random.choice(['TRX', 'USDT', 'USDC'])
            
            token_name = token_names.get(token_symbol, token_symbol)
            
            # Random amounts
            if token_symbol in ['ETH', 'BNB', 'TRX']:
                amount = Decimal(str(random.uniform(0.1, 5.0)))
            else:  # Stablecoins
                amount = Decimal(str(random.uniform(10, 1000)))
            
            # Random addresses
            from_addr = f"0x{''.join(random.choices('0123456789abcdef', k=40))}" if wallet.network != 'TRC' else f"T{''.join(random.choices('0123456789ABCDEFGHJKLMNPQRSTUVWXYZ', k=33))}"
            to_addr = wallet.wallet_address if tx_type == 'IN' else f"0x{''.join(random.choices('0123456789abcdef', k=40))}" if wallet.network != 'TRC' else f"T{''.join(random.choices('0123456789ABCDEFGHJKLMNPQRSTUVWXYZ', k=33))}"
            
            if tx_type == 'INTERNAL':
                from_addr = wallet.wallet_address
                to_addr = wallet.wallet_address
            
            sample_tx = {
                'transaction_hash': tx_hash,
                'block_number': random.randint(18000000, 19000000),
                'block_timestamp': base_time - timedelta(hours=random.randint(1, 168)),  # Random time in last week
                'from_address': from_addr,
                'to_address': to_addr,
                'token_symbol': token_symbol,
                'token_name': token_name,
                'token_address': None if token_symbol in ['ETH', 'BNB', 'TRX'] else f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
                'token_amount': amount,
                'token_decimals': 18 if token_symbol in ['ETH', 'BNB'] else 6 if token_symbol in ['USDT', 'USDC'] else 6,
                'transaction_type': tx_type,
                'gas_fee': Decimal(str(random.uniform(0.001, 0.01))),
                'gas_fee_token': 'ETH' if wallet.network == 'ETH' else 'BNB' if wallet.network == 'BSC' else 'TRX',
                'status': random.choice(['CONFIRMED', 'CONFIRMED', 'CONFIRMED', 'PENDING']),  # Mostly confirmed
                'confirmations': random.randint(12, 1000),
                'network': wallet.network
            }
            
            sample_transactions.append(sample_tx)
        
        return sample_transactions
    
    def sync_all_wallets(self, force_full_sync: bool = False) -> Dict:
        """Sync all active wallets"""
        try:
            wallets = self.get_all_wallets(active_only=True)
            results = []
            
            for wallet in wallets:
                try:
                    result = self.sync_wallet_transactions(wallet.id, force_full_sync)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error syncing wallet {wallet.wallet_name}: {e}")
                    results.append({
                        'wallet_id': wallet.id,
                        'wallet_name': wallet.wallet_name,
                        'error': str(e)
                    })
            
            return {
                'total_wallets': len(wallets),
                'successful_syncs': len([r for r in results if 'error' not in r]),
                'failed_syncs': len([r for r in results if 'error' in r]),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in sync_all_wallets: {e}")
            raise
    
    def get_wallet_transactions(self, wallet_id: int, page: int = 1, per_page: int = 50, 
                              start_date: datetime = None, end_date: datetime = None,
                              token_symbol: str = None, transaction_type: str = None) -> Dict:
        """Get transactions for a wallet with pagination and filters"""
        try:
            query = TrustWalletTransaction.query.filter_by(wallet_id=wallet_id)
            
            # Apply filters
            if start_date:
                query = query.filter(TrustWalletTransaction.block_timestamp >= start_date)
            if end_date:
                query = query.filter(TrustWalletTransaction.block_timestamp <= end_date)
            if token_symbol:
                query = query.filter(TrustWalletTransaction.token_symbol == token_symbol)
            if transaction_type:
                query = query.filter(TrustWalletTransaction.transaction_type == transaction_type)
            
            # Get total count
            total_count = query.count()
            logger.info(f"Found {total_count} total transactions for wallet_id={wallet_id}")
            
            # Apply pagination
            transactions = query.order_by(desc(TrustWalletTransaction.block_timestamp))\
                              .offset((page - 1) * per_page)\
                              .limit(per_page)\
                              .all()
            
            logger.info(f"Returning {len(transactions)} transactions for wallet_id={wallet_id}, page={page}")
            
            return {
                'transactions': [tx.to_dict() for tx in transactions],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting wallet transactions: {e}")
            raise
    
    def get_wallet_summary(self, wallet_id: int, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """Get summary statistics for a wallet"""
        try:
            wallet = TrustWallet.query.get(wallet_id)
            if not wallet:
                raise ValueError(f"Wallet with ID {wallet_id} not found")
            
            # Get summary data
            summary = TrustWalletTransaction.get_wallet_summary(wallet_id, start_date, end_date)
            
            # Get token breakdown
            token_query = TrustWalletTransaction.query.filter_by(wallet_id=wallet_id)
            if start_date:
                token_query = token_query.filter(TrustWalletTransaction.block_timestamp >= start_date)
            if end_date:
                token_query = token_query.filter(TrustWalletTransaction.block_timestamp <= end_date)
            
            token_summary = token_query.with_entities(
                TrustWalletTransaction.token_symbol,
                db.func.count(TrustWalletTransaction.id).label('count'),
                db.func.sum(TrustWalletTransaction.token_amount).label('total_amount'),
                db.func.sum(TrustWalletTransaction.amount_try).label('total_amount_try')
            ).group_by(TrustWalletTransaction.token_symbol).all()
            
            return {
                'wallet_id': wallet_id,
                'wallet_name': wallet.wallet_name,
                'wallet_address': wallet.wallet_address,
                'network': wallet.network,
                'summary': {
                    'transaction_count': summary.transaction_count or 0,
                    'total_amount': float(summary.total_amount or 0),
                    'total_amount_try': float(summary.total_amount_try or 0),
                    'total_gas_fee': float(summary.total_gas_fee or 0),
                    'total_gas_fee_try': float(summary.total_gas_fee_try or 0),
                    'unique_tokens': summary.unique_tokens or 0
                },
                'token_breakdown': [
                    {
                        'token_symbol': token.token_symbol,
                        'transaction_count': token.count,
                        'total_amount': float(token.total_amount or 0),
                        'total_amount_try': float(token.total_amount_try or 0)
                    }
                    for token in token_summary
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting wallet summary: {e}")
            raise
    
    def get_all_transactions_summary(self, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """Get summary for all wallets combined"""
        try:
            query = TrustWalletTransaction.query.join(TrustWallet)
            
            if start_date:
                query = query.filter(TrustWalletTransaction.block_timestamp >= start_date)
            if end_date:
                query = query.filter(TrustWalletTransaction.block_timestamp <= end_date)
            
            # Overall summary
            overall_summary = query.with_entities(
                db.func.count(TrustWalletTransaction.id).label('total_transactions'),
                db.func.sum(TrustWalletTransaction.amount_try).label('total_amount_try'),
                db.func.sum(TrustWalletTransaction.gas_fee_try).label('total_gas_fee_try'),
                db.func.count(db.func.distinct(TrustWalletTransaction.wallet_id)).label('active_wallets'),
                db.func.count(db.func.distinct(TrustWalletTransaction.token_symbol)).label('unique_tokens')
            ).first()
            
            # Network breakdown
            network_summary = query.with_entities(
                TrustWalletTransaction.network,
                db.func.count(TrustWalletTransaction.id).label('count'),
                db.func.sum(TrustWalletTransaction.amount_try).label('total_amount_try')
            ).group_by(TrustWalletTransaction.network).all()
            
            # Token breakdown
            token_summary = query.with_entities(
                TrustWalletTransaction.token_symbol,
                db.func.count(TrustWalletTransaction.id).label('count'),
                db.func.sum(TrustWalletTransaction.token_amount).label('total_amount'),
                db.func.sum(TrustWalletTransaction.amount_try).label('total_amount_try')
            ).group_by(TrustWalletTransaction.token_symbol).all()
            
            return {
                'overall': {
                    'total_transactions': overall_summary.total_transactions or 0,
                    'total_amount_try': float(overall_summary.total_amount_try or 0),
                    'total_gas_fee_try': float(overall_summary.total_gas_fee_try or 0),
                    'active_wallets': overall_summary.active_wallets or 0,
                    'unique_tokens': overall_summary.unique_tokens or 0
                },
                'by_network': [
                    {
                        'network': network.network,
                        'transaction_count': network.count,
                        'total_amount_try': float(network.total_amount_try or 0)
                    }
                    for network in network_summary
                ],
                'by_token': [
                    {
                        'token_symbol': token.token_symbol,
                        'transaction_count': token.count,
                        'total_amount': float(token.total_amount or 0),
                        'total_amount_try': float(token.total_amount_try or 0)
                    }
                    for token in token_summary
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting all transactions summary: {e}")
            raise
    
    def get_wallet_balance(self, wallet_id: int) -> Dict:
        """Get wallet balance for a specific wallet"""
        try:
            wallet = TrustWallet.query.get(wallet_id)
            if not wallet:
                raise ValueError(f"Wallet with ID {wallet_id} not found")
            
            if not wallet.is_active:
                raise ValueError(f"Wallet {wallet.wallet_name} is not active")
            
            logger.info(f"Getting balance for wallet: {wallet.wallet_name} ({wallet.network})")
            
            # Fetch real balances from blockchain API
            try:
                real_balances = self.blockchain_api.get_wallet_balance(
                    wallet_address=wallet.wallet_address,
                    network=wallet.network
                )
                logger.info(f"Fetched balances for {wallet.wallet_name}: {real_balances}")
            except Exception as api_error:
                logger.error(f"Error fetching real balances, falling back to sample data: {api_error}")
                # Fallback to sample data if API fails
                real_balances = self._create_sample_balances(wallet)
            
            # Add USD conversion for each token
            balances_with_usd = {}
            total_usd = 0.0
            for token, amount in real_balances.items():
                usd_value = self._get_token_usd_value(token, amount)
                
                # Filter out unknown tokens with USD value less than 0.1
                if token.startswith('UNKNOWN_') and usd_value < 0.1:
                    logger.info(f"Filtering out unknown token {token} with USD value ${usd_value:.6f} (below $0.1 threshold)")
                    continue
                
                balances_with_usd[token] = {
                    'amount': amount,
                    'usd_value': usd_value
                }
                total_usd += usd_value
            
            return {
                'wallet_id': wallet_id,
                'wallet_name': wallet.wallet_name,
                'network': wallet.network,
                'balances': balances_with_usd,
                'total_usd': round(total_usd, 2),
                'last_updated': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error getting wallet balance {wallet_id}: {e}")
            raise
    
    def _get_token_usd_value(self, token: str, amount: float) -> float:
        """Get USD value for a token amount using CoinGecko API"""
        import requests
        import time
        
        # Crypto to CoinGecko ID mapping
        token_map = {
            'TRX': 'tron',
            'USDT': 'tether',
            'USDC': 'usd-coin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'BTC': 'bitcoin'
        }
        
        # If USDT or USDC, 1:1 with USD
        if token in ['USDT', 'USDC']:
            return round(amount, 2)
        
        # Try to get price from CoinGecko
        coin_id = token_map.get(token)
        if not coin_id:
            logger.warning(f"No price mapping for token {token}")
            return 0.0
        
        try:
            # CoinGecko free API (no key needed)
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                price = data.get(coin_id, {}).get('usd', 0)
                return round(amount * price, 2)
            else:
                logger.warning(f"CoinGecko API returned {response.status_code}")
                return 0.0
                
        except Exception as e:
            logger.warning(f"Error fetching token price for {token}: {e}")
            return 0.0
    
    def _create_sample_balances(self, wallet: TrustWallet) -> Dict[str, float]:
        """Create sample balances for demonstration"""
        import random
        
        balances = {}
        
        if wallet.network == 'ETH':
            balances['ETH'] = round(random.uniform(0.1, 5.0), 4)
            balances['USDT'] = round(random.uniform(100, 2000), 2)
            balances['USDC'] = round(random.uniform(50, 1000), 2)
            if random.random() > 0.5:
                balances['WBTC'] = round(random.uniform(0.01, 0.5), 4)
        elif wallet.network == 'BSC':
            balances['BNB'] = round(random.uniform(0.5, 10.0), 4)
            balances['USDT'] = round(random.uniform(200, 3000), 2)
            balances['USDC'] = round(random.uniform(100, 1500), 2)
            if random.random() > 0.5:
                balances['CAKE'] = round(random.uniform(10, 100), 2)
        elif wallet.network == 'TRC':
            balances['TRX'] = round(random.uniform(100, 5000), 2)
            balances['USDT'] = round(random.uniform(500, 5000), 2)
            if random.random() > 0.5:
                balances['USDC'] = round(random.uniform(100, 1000), 2)
        
        return balances
