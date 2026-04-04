import React, { useEffect, useState, useCallback } from 'react';
import { StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { WardrobeHeader, WardrobeList } from '../components/wardrobe';
import { AddItemModal } from '../components/AddItemModal';
import { ItemDetailModal } from '../components/ItemDetailModal';
import { useWardrobeStore } from '../stores';
import type { ClothingItem } from '../types';

export const WardrobeScreen: React.FC = () => {
  const [showAdd, setShowAdd] = useState(false);
  const [selected, setSelected] = useState<ClothingItem | null>(null);
  const fetchItems = useWardrobeStore((s) => s.fetchItems);

  useEffect(() => { fetchItems(true); }, [fetchItems]);

  const handleItemPress = useCallback((item: ClothingItem) => setSelected(item), []);

  return (
    <ErrorBoundary>
      <SafeAreaView style={styles.container} edges={['top']}>
        <WardrobeHeader onAddPress={() => setShowAdd(true)} />
        <WardrobeList onItemPress={handleItemPress} />
        <AddItemModal visible={showAdd} onClose={() => setShowAdd(false)} />
        {selected && <ItemDetailModal item={selected} visible onClose={() => setSelected(null)} />}
      </SafeAreaView>
    </ErrorBoundary>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
});
