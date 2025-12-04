import React, { useState } from 'react';
import { X, Wallet, AlertCircle, CheckCircle } from 'lucide-react';
import { Button, Input, Label, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui';
import { useLanguage } from '../../contexts/LanguageContext';
import { api } from '../../utils/apiClient';

interface AddWalletModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (walletId?: number) => void;
}

interface WalletFormData {
  wallet_address: string;
  wallet_name: string;
  network: string;
}

const AddWalletModal: React.FC<AddWalletModalProps> = ({
  isOpen,
  onClose,
  onSuccess
}) => {
  const { t } = useLanguage();
  const [formData, setFormData] = useState<WalletFormData>({
    wallet_address: '',
    wallet_name: '',
    network: 'ETH'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Partial<WalletFormData>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  const validateForm = (): boolean => {
    const newErrors: Partial<WalletFormData> = {};

    if (!formData.wallet_name.trim()) {
      newErrors.wallet_name = 'Wallet name is required';
    }

    if (!formData.wallet_address.trim()) {
      newErrors.wallet_address = 'Wallet address is required';
    } else {
      // Basic validation for different networks
      if (formData.network === 'ETH' || formData.network === 'BSC') {
        if (!formData.wallet_address.startsWith('0x') || formData.wallet_address.length !== 42) {
          newErrors.wallet_address = 'Invalid Ethereum/BSC address format';
        }
      } else if (formData.network === 'TRC') {
        if (!formData.wallet_address.startsWith('T') || formData.wallet_address.length !== 34) {
          newErrors.wallet_address = 'Invalid TRON address format';
        }
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const response = await api.post('/trust-wallet/wallets', formData);
      
      // Parse the response properly
      const responseData = await api.parseResponse<{success: boolean; wallet?: any; error?: string}>(response);
      
      if (responseData.success) {
        const walletId = responseData.wallet?.id;
        onSuccess(walletId);
        onClose();
        setFormData({ wallet_address: '', wallet_name: '', network: 'ETH' });
        setErrors({});
      } else {
        setSubmitError(responseData.error || 'Failed to create wallet');
      }
    } catch (error) {
      console.error('Error creating wallet:', error);
      
      // Try to parse error message for better user feedback
      if (error instanceof Error) {
        if (error.message.includes('409') || error.message.includes('already exists')) {
          setSubmitError('This wallet address is already registered. Please use a different address.');
          // Clear the wallet address field to make it easier to try a different one
          setFormData(prev => ({ ...prev, wallet_address: '' }));
        } else if (error.message.includes('400') || error.message.includes('Invalid')) {
          setSubmitError('Invalid wallet address format. Please check the address and try again.');
        } else if (error.message.includes('Network error') || error.message.includes('fetch')) {
          setSubmitError('Network error. Please check your connection and try again.');
        } else if (error.message.includes('500')) {
          setSubmitError('Server error. Please try again later.');
        } else {
          setSubmitError(error.message || 'Failed to create wallet. Please try again.');
        }
      } else {
        setSubmitError('Network error. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
      setFormData({ wallet_address: '', wallet_name: '', network: 'ETH' });
      setErrors({});
      setSubmitError(null);
    }
  };

  const getAddressPlaceholder = () => {
    switch (formData.network) {
      case 'ETH':
        return '0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b7';
      case 'BSC':
        return '0x8ba1f109551bD432803012645Hac136c13';
      case 'TRC':
        return 'TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE';
      default:
        return 'Enter wallet address';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Wallet className="h-5 w-5 text-blue-600" />
            Add New Wallet
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {submitError && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-md">
              <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-red-700">
                <p>{submitError}</p>
                {submitError.includes('already registered') && (
                  <p className="mt-1 text-xs text-red-600">
                    💡 Tip: Check if you've already added this wallet or try a different address.
                  </p>
                )}
              </div>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="wallet_name">Wallet Name</Label>
            <Input
              id="wallet_name"
              value={formData.wallet_name}
              onChange={(e) => setFormData({ ...formData, wallet_name: e.target.value })}
              placeholder="e.g., Main Company Wallet"
              className={errors.wallet_name ? 'border-red-300' : ''}
            />
            {errors.wallet_name && (
              <p className="text-sm text-red-600">{errors.wallet_name}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="network">Network</Label>
            <Select
              value={formData.network}
              onValueChange={(value) => setFormData({ ...formData, network: value })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select network" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ETH">Ethereum (ETH)</SelectItem>
                <SelectItem value="BSC">Binance Smart Chain (BSC)</SelectItem>
                <SelectItem value="TRC">TRON (TRC)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="wallet_address">Wallet Address</Label>
            <Input
              id="wallet_address"
              value={formData.wallet_address}
              onChange={(e) => setFormData({ ...formData, wallet_address: e.target.value })}
              placeholder={getAddressPlaceholder()}
              className={errors.wallet_address ? 'border-red-300' : ''}
            />
            {errors.wallet_address && (
              <p className="text-sm text-red-600">{errors.wallet_address}</p>
            )}
            <p className="text-xs text-gray-500">
              {formData.network === 'ETH' || formData.network === 'BSC' 
                ? 'Must start with 0x and be 42 characters long'
                : 'Must start with T and be 34 characters long'
              }
            </p>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Creating...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Create Wallet
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default AddWalletModal;
