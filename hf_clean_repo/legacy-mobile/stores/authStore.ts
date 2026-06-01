export interface LegacyAuthState {
  readonly deprecated: true;
}

export const useAuthStore = (): LegacyAuthState => {
  throw new Error(
    'stores/authStore.ts is part of a legacy React Native scaffold. Use frontend/ as the active app source of truth.'
  );
};
