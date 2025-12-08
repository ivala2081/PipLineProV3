import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { 
  User, 
  Mail, 
  Phone, 
  Building2, 
  DollarSign, 
  Calendar,
  CreditCard,
  FileText,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'tel' | 'number' | 'date' | 'select' | 'textarea';
  placeholder?: string;
  required?: boolean;
  options?: { value: string; label: string }[];
  icon?: React.ReactNode;
}

interface ModernFormProps {
  title: string;
  description?: string;
  fields: FormField[];
  onSubmit: (data: any) => void;
  submitLabel?: string;
  loading?: boolean;
  initialData?: any;
}

export const ModernForm: React.FC<ModernFormProps> = ({
  title,
  description,
  fields,
  onSubmit,
  submitLabel = 'Submit',
  loading = false,
  initialData = {}
}) => {
  const [formData, setFormData] = useState(initialData);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const handleChange = (name: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleBlur = (name: string) => {
    setTouched(prev => ({ ...prev, [name]: true }));
  };

  const validateField = (field: FormField, value: any): string => {
    if (field.required && (!value || value.toString().trim() === '')) {
      return `${field.label} is required`;
    }

    if (field.type === 'email' && value) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(value)) {
        return 'Please enter a valid email address';
      }
    }

    if (field.type === 'tel' && value) {
      const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
      if (!phoneRegex.test(value.replace(/[\s\-\(\)]/g, ''))) {
        return 'Please enter a valid phone number';
      }
    }

    if (field.type === 'number' && value) {
      if (isNaN(Number(value)) || Number(value) < 0) {
        return 'Please enter a valid number';
      }
    }

    return '';
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    let isValid = true;

    fields.forEach(field => {
      const error = validateField(field, formData[field.name]);
      if (error) {
        newErrors[field.name] = error;
        isValid = false;
      }
    });

    setErrors(newErrors);
    return isValid;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const getFieldIcon = (type: string) => {
    const iconMap = {
      text: User,
      email: Mail,
      tel: Phone,
      number: DollarSign,
      date: Calendar,
      select: Building2,
      textarea: FileText
    };
    
    const IconComponent = iconMap[type as keyof typeof iconMap] || User;
    return <IconComponent className="w-4 h-4" />;
  };

  const renderField = (field: FormField) => {
    const hasError = touched[field.name] && errors[field.name];
    const fieldIcon = field.icon || getFieldIcon(field.type);

    return (
      <div key={field.name} className="space-y-2">
        <label className="text-sm font-medium text-foreground flex items-center gap-2">
          {fieldIcon}
          {field.label}
          {field.required && <span className="text-destructive">*</span>}
        </label>
        
        {field.type === 'select' ? (
          <select
            value={formData[field.name] || ''}
            onChange={(e) => handleChange(field.name, e.target.value)}
            onBlur={() => handleBlur(field.name)}
            className={`w-full px-3 py-2 border rounded-md bg-background text-foreground ${
              hasError ? 'border-destructive' : 'border-input'
            } focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2`}
          >
            <option value="">Select {field.label}</option>
            {field.options?.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        ) : field.type === 'textarea' ? (
          <textarea
            value={formData[field.name] || ''}
            onChange={(e) => handleChange(field.name, e.target.value)}
            onBlur={() => handleBlur(field.name)}
            placeholder={field.placeholder}
            rows={4}
            className={`w-full px-3 py-2 border rounded-md bg-background text-foreground resize-none ${
              hasError ? 'border-destructive' : 'border-input'
            } focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2`}
          />
        ) : (
          <Input
            type={field.type}
            value={formData[field.name] || ''}
            onChange={(e) => handleChange(field.name, e.target.value)}
            onBlur={() => handleBlur(field.name)}
            placeholder={field.placeholder}
            className={hasError ? 'border-destructive' : ''}
          />
        )}
        
        {hasError && (
          <div className="flex items-center gap-1 text-sm text-destructive">
            <AlertCircle className="w-4 h-4" />
            {errors[field.name]}
          </div>
        )}
      </div>
    );
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="w-5 h-5" />
          {title}
        </CardTitle>
        {description && (
          <CardDescription>{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {fields.map(renderField)}
          </div>
          
          <div className="flex items-center justify-between pt-4 border-t border-border">
            <div className="text-sm text-muted-foreground">
              Fields marked with <span className="text-destructive">*</span> are required
            </div>
            <div className="flex gap-3">
              <Button type="button" variant="outline">
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Processing...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    {submitLabel}
                  </>
                )}
              </Button>
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};
