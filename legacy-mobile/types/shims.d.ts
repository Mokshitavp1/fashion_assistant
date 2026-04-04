declare module 'react-native-url-polyfill/auto';

declare namespace NodeJS {
    interface ProcessEnv {
        EXPO_PUBLIC_SUPABASE_URL?: string;
        EXPO_PUBLIC_SUPABASE_ANON_KEY?: string;
    }
}

declare module 'isomorphic-dompurify' {
    const DOMPurify: any;
    export default DOMPurify;
}
