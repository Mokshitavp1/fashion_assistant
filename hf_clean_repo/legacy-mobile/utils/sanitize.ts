import DOMPurify from 'isomorphic-dompurify';

/**
 * Sanitizes string input to prevent XSS and injection attacks
 */
export const sanitizeString = (input: string | null | undefined): string => {
    if (!input) return '';
    return input
        .trim()
        .replace(/[<>]/g, '') // Remove angle brackets
        .replace(/javascript:/gi, '') // Remove javascript: protocol
        .replace(/on\w+=/gi, '') // Remove event handlers
        .slice(0, 1000); // Limit length
};

/**
 * Sanitizes all string properties in an object
 */
export const sanitizeObject = <T extends Record<string, unknown>>(obj: T): T => {
    const result = { ...obj };
    for (const key in result) {
        if (typeof result[key] === 'string') {
            (result as Record<string, unknown>)[key] = sanitizeString(result[key] as string);
        }
    }
    return result;
};

/**
 * Validates email format
 */
export const validateEmail = (email: string): boolean => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
};

/**
 * Sanitizes URL - only allows http/https
 */
export const sanitizeUrl = (url: string | null | undefined): string => {
    if (!url) return '';
    try {
        const parsed = new URL(url);
        return ['http:', 'https:'].includes(parsed.protocol) ? parsed.toString() : '';
    } catch {
        return '';
    }
};
