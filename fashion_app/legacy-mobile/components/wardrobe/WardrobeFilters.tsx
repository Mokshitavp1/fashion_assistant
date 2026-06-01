import React, { memo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useWardrobeStore } from '../../stores';
import { CATEGORIES, COLORS, SEASONS } from '../../constants';
import type { Category } from '../../types';

interface FilterChipProps {
  label: string;
  active: boolean;
  onPress: () => void;
}

const FilterChip: React.FC<FilterChipProps> = memo(({ label, active, onPress }) => (
  <TouchableOpacity
    style={[styles.chip, active && styles.chipActive]}
    onPress={onPress}
  >
    <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
  </TouchableOpacity>
));

FilterChip.displayName = 'FilterChip';

export const WardrobeFilters: React.FC = memo(() => {
  const { filters, setFilters } = useWardrobeStore();

  return (
    <View style={styles.container}>
      <Text style={styles.sectionTitle}>Category</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipRow}>
        <FilterChip
          label="All"
          active={filters.category === 'all'}
          onPress={() => setFilters({ category: 'all' })}
        />
        {CATEGORIES.map((cat) => (
          <FilterChip
            key={cat.value}
            label={cat.label}
            active={filters.category === cat.value}
            onPress={() => setFilters({ category: cat.value as Category })}
          />
        ))}
      </ScrollView>

      <Text style={styles.sectionTitle}>Season</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipRow}>
        <FilterChip
          label="All"
          active={filters.season === 'all'}
          onPress={() => setFilters({ season: 'all' })}
        />
        {SEASONS.map((season) => (
          <FilterChip
            key={season.value}
            label={season.label}
            active={filters.season === season.value}
            onPress={() => setFilters({ season: season.value })}
          />
        ))}
      </ScrollView>
    </View>
  );
});

WardrobeFilters.displayName = 'WardrobeFilters';

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
    marginTop: 8,
  },
  chipRow: {
    flexDirection: 'row',
    marginBottom: 4,
  },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    marginRight: 8,
  },
  chipActive: {
    backgroundColor: '#8B5CF6',
  },
  chipText: {
    fontSize: 14,
    color: '#6B7280',
  },
  chipTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
});
