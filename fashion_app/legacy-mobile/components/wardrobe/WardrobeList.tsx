import React, { memo, useCallback } from 'react';
import { FlatList, StyleSheet, ActivityIndicator, View, Text, RefreshControl } from 'react-native';
import { useWardrobeStore } from '../../stores';
import { ClothingItemCard } from '../ClothingItemCard';
import type { ClothingItem } from '../../types';

interface Props {
  onItemPress: (item: ClothingItem) => void;
}

export const WardrobeList: React.FC<Props> = memo(({ onItemPress }) => {
  const { items, loading, error, hasMore, fetchItems, selectedIds, toggleSelect } = useWardrobeStore();

  const handleLoadMore = useCallback(() => { if (!loading && hasMore) fetchItems(); }, [loading, hasMore, fetchItems]);

  const renderItem = useCallback(({ item }: { item: ClothingItem }) => (
    <ClothingItemCard
      item={item}
      onPress={() => onItemPress(item)}
      onLongPress={() => toggleSelect(item.id)}
      selected={selectedIds.has(item.id)}
    />
  ), [onItemPress, toggleSelect, selectedIds]);

  if (error) return <Text style={styles.error}>{error}</Text>;

  return (
    <FlatList
      data={items}
      renderItem={renderItem}
      keyExtractor={(i) => i.id}
      numColumns={2}
      contentContainerStyle={styles.list}
      columnWrapperStyle={styles.row}
      onEndReached={handleLoadMore}
      onEndReachedThreshold={0.3}
      ListFooterComponent={loading ? <ActivityIndicator style={styles.loader} color="#8B5CF6" /> : null}
      ListEmptyComponent={!loading ? <Text style={styles.empty}>No items yet</Text> : null}
      refreshControl={<RefreshControl refreshing={loading && !items.length} onRefresh={() => fetchItems(true)} tintColor="#8B5CF6" />}
      removeClippedSubviews
      maxToRenderPerBatch={10}
      windowSize={5}
    />
  );
});

WardrobeList.displayName = 'WardrobeList';

const styles = StyleSheet.create({
  list: { padding: 8, flexGrow: 1 },
  row: { justifyContent: 'space-between' },
  loader: { padding: 16 },
  empty: { textAlign: 'center', color: '#6B7280', marginTop: 32 },
  error: { textAlign: 'center', color: '#EF4444', margin: 16 },
});
