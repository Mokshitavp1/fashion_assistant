import React, { memo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LazyImage } from './LazyImage';
import type { ClothingItem } from '../types';

interface Props {
  item: ClothingItem;
  onPress: () => void;
  onLongPress?: () => void;
  selected?: boolean;
}

export const ClothingItemCard: React.FC<Props> = memo(({
  item,
  onPress,
  onLongPress,
  selected = false
}) => {
  return (
    <TouchableOpacity
      style={[styles.container, selected && styles.selected]}
      onPress={onPress}
      onLongPress={onLongPress}
      activeOpacity={0.7}
    >
      {selected && (
        <View style={styles.check}>
          <Ionicons name="checkmark-circle" size={24} color="#8B5CF6" />
        </View>
      )}

      <LazyImage
        uri={item.image_url}
        style={styles.image}
      />

      <View style={styles.info}>
        <Text style={styles.name} numberOfLines={1}>{item.item_name}</Text>
        {item.brand && (
          <Text style={styles.brand} numberOfLines={1}>{item.brand}</Text>
        )}
      </View>
    </TouchableOpacity>
  );
});

ClothingItemCard.displayName = 'ClothingItemCard';

const styles = StyleSheet.create({
  container: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 12,
    overflow: 'hidden',
    elevation: 2,
  },
  selected: {
    borderWidth: 2,
    borderColor: '#8B5CF6',
  },
  check: {
    position: 'absolute',
    top: 8,
    right: 8,
    zIndex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
  },
  image: {
    width: '100%',
    height: 150,
  },
  info: {
    padding: 12,
  },
  name: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  brand: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
});
