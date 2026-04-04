import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Props {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorMessage: React.FC<Props> = ({ message, onRetry, onDismiss }) => (
  <View style={styles.container}>
    <Ionicons name="alert-circle" size={20} color="#DC2626" />
    <Text style={styles.text}>{message}</Text>
    {onRetry && (
      <TouchableOpacity onPress={onRetry}>
        <Text style={styles.retry}>Retry</Text>
      </TouchableOpacity>
    )}
    {onDismiss && (
      <TouchableOpacity onPress={onDismiss}>
        <Ionicons name="close" size={20} color="#6B7280" />
      </TouchableOpacity>
    )}
  </View>
);

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF2F2',
    padding: 12,
    margin: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FECACA',
    gap: 8,
  },
  text: {
    flex: 1,
    color: '#DC2626',
    fontSize: 14,
  },
  retry: {
    color: '#8B5CF6',
    fontWeight: '600',
  },
});
