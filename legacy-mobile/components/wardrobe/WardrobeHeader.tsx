import React, { memo, useState, useCallback } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useWardrobeStore } from '../../stores';
import { useDebouncedCallback } from '../../hooks/useDebounce';
import { DEBOUNCE_MS } from '../../constants';

interface Props {
  onAddPress: () => void;
}

export const WardrobeHeader: React.FC<Props> = memo(({ onAddPress }) => {
  const { items, setFilters } = useWardrobeStore();
  const [showSearch, setShowSearch] = useState(false);
  const [text, setText] = useState('');

  const debouncedSearch = useDebouncedCallback((q: string) => setFilters({ searchQuery: q }), DEBOUNCE_MS);

  const handleChange = useCallback((t: string) => {
    setText(t);
    debouncedSearch(t);
  }, [debouncedSearch]);

  return (
    <View style={styles.container}>
      <View style={styles.row}>
        <Text style={styles.title}>My Wardrobe</Text>
        <Text style={styles.count}>{items.length} items</Text>
      </View>
      {showSearch ? (
        <View style={styles.searchRow}>
          <TextInput style={styles.input} placeholder="Search..." value={text} onChangeText={handleChange} autoFocus />
          <TouchableOpacity onPress={() => { setShowSearch(false); setText(''); setFilters({ searchQuery: '' }); }}>
            <Ionicons name="close" size={24} color="#6B7280" />
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.actions}>
          <TouchableOpacity onPress={() => setShowSearch(true)}><Ionicons name="search" size={22} color="#6B7280" /></TouchableOpacity>
          <TouchableOpacity style={styles.addBtn} onPress={onAddPress}><Ionicons name="add" size={24} color="#fff" /></TouchableOpacity>
        </View>
      )}
    </View>
  );
});

WardrobeHeader.displayName = 'WardrobeHeader';

const styles = StyleSheet.create({
  container: { padding: 16, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#E5E7EB' },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  title: { fontSize: 24, fontWeight: '700', color: '#1F2937' },
  count: { fontSize: 14, color: '#6B7280' },
  actions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 12 },
  searchRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  input: { flex: 1, height: 40, backgroundColor: '#F3F4F6', borderRadius: 8, paddingHorizontal: 12 },
  addBtn: { backgroundColor: '#8B5CF6', width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center' },
});
