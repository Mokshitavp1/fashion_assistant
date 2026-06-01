import { create } from 'zustand';
import { supabase } from '../lib/supabase';
import { sanitizeObject } from '../utils/sanitize';
import { PAGE_SIZE } from '../constants';
import type { ClothingItem } from '../types';

interface Filters {
  category: string | null;
  season: string | null;
  searchQuery: string;
}

interface WardrobeState {
  items: ClothingItem[];
  loading: boolean;
  error: string | null;
  page: number;
  hasMore: boolean;
  filters: Filters;
  selectedIds: Set<string>;

  fetchItems: (reset?: boolean) => Promise<void>;
  addItem: (item: Omit<ClothingItem, 'id' | 'created_at' | 'user_id'>) => Promise<void>;
  updateItem: (id: string, updates: Partial<ClothingItem>) => Promise<void>;
  deleteItem: (id: string) => Promise<void>;
  setFilters: (filters: Partial<Filters>) => void;
  toggleSelect: (id: string) => void;
  clearSelection: () => void;
  clearError: () => void;
}

export const useWardrobeStore = create<WardrobeState>((set, get) => ({
  items: [],
  loading: false,
  error: null,
  page: 0,
  hasMore: true,
  filters: { category: null, season: null, searchQuery: '' },
  selectedIds: new Set(),

  fetchItems: async (reset = false) => {
    const { loading, page, filters, items } = get();
    if (loading) return;

    const currentPage = reset ? 0 : page;
    set({ loading: true, error: null });

    try {
      let query = supabase
        .from('wardrobe_items')
        .select('*')
        .order('created_at', { ascending: false })
        .range(currentPage * PAGE_SIZE, (currentPage + 1) * PAGE_SIZE - 1);

      if (filters.category) query = query.eq('category', filters.category);
      if (filters.season) query = query.eq('season', filters.season);
      if (filters.searchQuery) {
        query = query.or(`item_name.ilike.%${filters.searchQuery}%,brand.ilike.%${filters.searchQuery}%`);
      }

      const { data, error } = await query;
      if (error) throw error;

      set({
        items: reset ? (data || []) : [...items, ...(data || [])],
        page: currentPage + 1,
        hasMore: (data?.length || 0) === PAGE_SIZE,
        loading: false,
      });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to fetch', loading: false });
    }
  },

  addItem: async (item) => {
    set({ loading: true, error: null });
    try {
      const sanitized = sanitizeObject(item);
      const { data, error } = await supabase.from('wardrobe_items').insert(sanitized).select().single();
      if (error) throw error;
      set((state) => ({ items: [data, ...state.items], loading: false }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to add', loading: false });
      throw err;
    }
  },

  updateItem: async (id, updates) => {
    const original = get().items.find((i) => i.id === id);
    set((state) => ({ items: state.items.map((i) => (i.id === id ? { ...i, ...updates } : i)) }));

    try {
      const { error } = await supabase.from('wardrobe_items').update(sanitizeObject(updates)).eq('id', id);
      if (error) throw error;
    } catch {
      if (original) set((state) => ({ items: state.items.map((i) => (i.id === id ? original : i)) }));
    }
  },

  deleteItem: async (id) => {
    const backup = get().items;
    set((state) => ({
      items: state.items.filter((i) => i.id !== id),
      selectedIds: new Set([...state.selectedIds].filter((sid) => sid !== id)),
    }));

    try {
      const { error } = await supabase.from('wardrobe_items').delete().eq('id', id);
      if (error) throw error;
    } catch {
      set({ items: backup });
    }
  },

  setFilters: (newFilters) => {
    set((state) => ({ filters: { ...state.filters, ...newFilters } }));
    get().fetchItems(true);
  },

  toggleSelect: (id) => {
    set((state) => {
      const s = new Set(state.selectedIds);
      s.has(id) ? s.delete(id) : s.add(id);
      return { selectedIds: s };
    });
  },

  clearSelection: () => set({ selectedIds: new Set() }),
  clearError: () => set({ error: null }),
}));
