// Input validation and sanitization utility
export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => boolean | string;
  sanitize?: (value: any) => any;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  sanitizedValue?: any;
}

export interface ValidationSchema {
  [key: string]: ValidationRule;
}

class Validator {
  private static readonly EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  private static readonly PHONE_PATTERN = /^[+]?[1-9][\d]{0,15}$/;
  private static readonly URL_PATTERN = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&//=]*)$/;
  private static readonly CURRENCY_PATTERN = /^\d+(\.\d{1,2})?$/;
  private static readonly DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

  /**
   * Validate a single field
   */
  static validateField(value: any, rule: ValidationRule): ValidationResult {
    const errors: string[] = [];
    let sanitizedValue = value;

    // Sanitize first if sanitizer is provided
    if (rule.sanitize) {
      try {
        sanitizedValue = rule.sanitize(value);
      } catch (error) {
        errors.push(`Sanitization failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }

    // Required check
    if (rule.required && (sanitizedValue === null || sanitizedValue === undefined || sanitizedValue === '')) {
      errors.push('This field is required');
      return { isValid: false, errors, sanitizedValue };
    }

    // Skip other validations if value is empty and not required
    if (!rule.required && (sanitizedValue === null || sanitizedValue === undefined || sanitizedValue === '')) {
      return { isValid: true, errors: [], sanitizedValue };
    }

    // Type-specific validations
    if (typeof sanitizedValue === 'string') {
      // Length validations
      if (rule.minLength && sanitizedValue.length < rule.minLength) {
        errors.push(`Minimum length is ${rule.minLength} characters`);
      }

      if (rule.maxLength && sanitizedValue.length > rule.maxLength) {
        errors.push(`Maximum length is ${rule.maxLength} characters`);
      }

      // Pattern validation
      if (rule.pattern && !rule.pattern.test(sanitizedValue)) {
        errors.push('Invalid format');
      }
    }

    // Custom validation
    if (rule.custom) {
      try {
        const result = rule.custom(sanitizedValue);
        if (result === false) {
          errors.push('Invalid value');
        } else if (typeof result === 'string') {
          errors.push(result);
        }
      } catch (error) {
        errors.push(`Validation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      sanitizedValue,
    };
  }

  /**
   * Validate an object against a schema
   */
  static validateObject(data: Record<string, any>, schema: ValidationSchema): ValidationResult {
    const errors: string[] = [];
    const sanitizedData: Record<string, any> = {};

    for (const [field, rule] of Object.entries(schema)) {
      const result = this.validateField(data[field], rule);
      
      if (!result.isValid) {
        errors.push(`${field}: ${result.errors.join(', ')}`);
      }
      
      if (result.sanitizedValue !== undefined) {
        sanitizedData[field] = result.sanitizedValue;
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      sanitizedValue: sanitizedData,
    };
  }

  /**
   * Predefined validation rules
   */
  static rules = {
    email: {
      required: true,
      pattern: Validator.EMAIL_PATTERN,
      sanitize: (value: string) => value.trim().toLowerCase(),
    } as ValidationRule,

    phone: {
      pattern: Validator.PHONE_PATTERN,
      sanitize: (value: string) => value.replace(/[\s\-()]/g, ''),
    } as ValidationRule,

    url: {
      pattern: Validator.URL_PATTERN,
      sanitize: (value: string) => value.trim(),
    } as ValidationRule,

    currency: {
      pattern: Validator.CURRENCY_PATTERN,
      custom: (value: string) => {
        const num = parseFloat(value);
        return !isNaN(num) && num >= 0 ? true : 'Must be a valid positive number';
      },
      sanitize: (value: string) => parseFloat(value).toFixed(2),
    } as ValidationRule,

    date: {
      pattern: Validator.DATE_PATTERN,
      custom: (value: string) => {
        const date = new Date(value);
        return !isNaN(date.getTime()) ? true : 'Must be a valid date';
      },
    } as ValidationRule,

    password: {
      required: true,
      minLength: 8,
      custom: (value: string) => {
        const hasUpperCase = /[A-Z]/.test(value);
        const hasLowerCase = /[a-z]/.test(value);
        const hasNumbers = /\d/.test(value);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(value);
        
        if (!hasUpperCase) return 'Must contain at least one uppercase letter';
        if (!hasLowerCase) return 'Must contain at least one lowercase letter';
        if (!hasNumbers) return 'Must contain at least one number';
        if (!hasSpecialChar) return 'Must contain at least one special character';
        
        return true;
      },
    } as ValidationRule,

    username: {
      required: true,
      minLength: 3,
      maxLength: 20,
      pattern: /^[a-zA-Z0-9_]+$/,
      sanitize: (value: string) => value.trim().toLowerCase(),
    } as ValidationRule,

    text: {
      maxLength: 1000,
      sanitize: (value: string) => value.trim(),
    } as ValidationRule,

    number: {
      custom: (value: any) => {
        const num = Number(value);
        return !isNaN(num) ? true : 'Must be a valid number';
      },
      sanitize: (value: any) => Number(value),
    } as ValidationRule,

    integer: {
      custom: (value: any) => {
        const num = Number(value);
        return !isNaN(num) && Number.isInteger(num) ? true : 'Must be a valid integer';
      },
      sanitize: (value: any) => Math.floor(Number(value)),
    } as ValidationRule,
  };

  /**
   * Sanitize HTML content to prevent XSS
   */
  static sanitizeHtml(html: string): string {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
  }

  /**
   * Sanitize object keys to prevent injection
   */
  static sanitizeObjectKeys(obj: Record<string, any>): Record<string, any> {
    const sanitized: Record<string, any> = {};
    
    for (const [key, value] of Object.entries(obj)) {
      const sanitizedKey = key.replace(/[^a-zA-Z0-9_]/g, '');
      if (sanitizedKey) {
        sanitized[sanitizedKey] = value;
      }
    }
    
    return sanitized;
  }

  /**
   * Validate and sanitize form data
   */
  static validateForm(formData: FormData, schema: ValidationSchema): ValidationResult {
    const data: Record<string, any> = {};
    
    // Convert FormData to object
    for (const [key, value] of formData.entries()) {
      data[key] = value;
    }
    
    return this.validateObject(data, schema);
  }
}

export default Validator;
