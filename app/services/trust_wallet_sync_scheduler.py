"""
Trust Wallet Sync Scheduler
Handles automatic syncing of Trust wallet transactions every 15 minutes
"""
import logging
import schedule
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List

from app import create_app
from app.services.trust_wallet_service import TrustWalletService
from app.models.trust_wallet import TrustWallet

logger = logging.getLogger(__name__)

class TrustWalletSyncScheduler:
    """Scheduler for automatic Trust wallet transaction syncing"""
    
    def __init__(self):
        self.app = create_app()
        self.trust_wallet_service = TrustWalletService()
        self.is_running = False
        self.sync_thread = None
        
    def start_scheduler(self):
        """Start the sync scheduler"""
        if self.is_running:
            logger.warning("Trust wallet sync scheduler is already running")
            return
        
        self.is_running = True
        
        # Schedule sync every 15 minutes
        schedule.every(15).minutes.do(self._sync_all_wallets_job)
        
        # Start the scheduler in a separate thread
        self.sync_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.sync_thread.start()
        
        logger.info("Trust wallet sync scheduler started (15-minute intervals)")
    
    def stop_scheduler(self):
        """Stop the sync scheduler"""
        if not self.is_running:
            logger.warning("Trust wallet sync scheduler is not running")
            return
        
        self.is_running = False
        schedule.clear()
        
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
        
        logger.info("Trust wallet sync scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def _sync_all_wallets_job(self):
        """Job to sync all active wallets"""
        with self.app.app_context():
            try:
                logger.info("Starting scheduled Trust wallet sync...")
                
                # Get all active wallets
                active_wallets = TrustWallet.query.filter_by(is_active=True).all()
                
                if not active_wallets:
                    logger.info("No active wallets found for sync")
                    return
                
                logger.info(f"Syncing {len(active_wallets)} active wallets")
                
                # Sync all wallets
                result = self.trust_wallet_service.sync_all_wallets(force_full_sync=False)
                
                # Log results
                successful = result['successful_syncs']
                failed = result['failed_syncs']
                
                logger.info(f"Scheduled sync completed: {successful} successful, {failed} failed")
                
                # Log details for failed syncs
                for sync_result in result['results']:
                    if 'error' in sync_result:
                        logger.error(f"Failed to sync wallet {sync_result['wallet_name']}: {sync_result['error']}")
                    else:
                        logger.debug(f"Synced wallet {sync_result['wallet_name']}: {sync_result['new_transactions']} new transactions")
                
            except Exception as e:
                logger.error(f"Error in scheduled sync job: {e}")
    
    def force_sync_all(self) -> Dict:
        """Force sync all wallets immediately"""
        with self.app.app_context():
            try:
                logger.info("Starting forced sync of all Trust wallets...")
                result = self.trust_wallet_service.sync_all_wallets(force_full_sync=True)
                logger.info(f"Forced sync completed: {result['successful_syncs']} successful, {result['failed_syncs']} failed")
                return result
            except Exception as e:
                logger.error(f"Error in forced sync: {e}")
                raise
    
    def force_sync_wallet(self, wallet_id: int) -> Dict:
        """Force sync a specific wallet immediately"""
        with self.app.app_context():
            try:
                logger.info(f"Starting forced sync for wallet ID {wallet_id}...")
                result = self.trust_wallet_service.sync_wallet_transactions(wallet_id, force_full_sync=True)
                logger.info(f"Forced sync completed for wallet {result['wallet_name']}: {result['new_transactions']} new transactions")
                return result
            except Exception as e:
                logger.error(f"Error in forced sync for wallet {wallet_id}: {e}")
                raise
    
    def get_sync_status(self) -> Dict:
        """Get current sync status"""
        with self.app.app_context():
            try:
                active_wallets = TrustWallet.query.filter_by(is_active=True).all()
                
                status = {
                    'scheduler_running': self.is_running,
                    'active_wallets_count': len(active_wallets),
                    'last_sync_times': [],
                    'next_scheduled_sync': None
                }
                
                # Get last sync times for each wallet
                for wallet in active_wallets:
                    status['last_sync_times'].append({
                        'wallet_id': wallet.id,
                        'wallet_name': wallet.wallet_name,
                        'network': wallet.network,
                        'last_sync_time': wallet.last_sync_time.isoformat() if wallet.last_sync_time else None,
                        'last_sync_block': wallet.last_sync_block
                    })
                
                # Get next scheduled sync time
                if schedule.jobs:
                    next_job = min(schedule.jobs, key=lambda x: x.next_run)
                    status['next_scheduled_sync'] = next_job.next_run.isoformat()
                
                return status
                
            except Exception as e:
                logger.error(f"Error getting sync status: {e}")
                raise

# Global scheduler instance
trust_wallet_scheduler = TrustWalletSyncScheduler()

def start_trust_wallet_sync():
    """Start the Trust wallet sync scheduler"""
    trust_wallet_scheduler.start_scheduler()

def stop_trust_wallet_sync():
    """Stop the Trust wallet sync scheduler"""
    trust_wallet_scheduler.stop_scheduler()

def get_trust_wallet_sync_status():
    """Get Trust wallet sync status"""
    return trust_wallet_scheduler.get_sync_status()

def force_sync_all_trust_wallets():
    """Force sync all Trust wallets"""
    return trust_wallet_scheduler.force_sync_all()

def force_sync_trust_wallet(wallet_id: int):
    """Force sync a specific Trust wallet"""
    return trust_wallet_scheduler.force_sync_wallet(wallet_id)
