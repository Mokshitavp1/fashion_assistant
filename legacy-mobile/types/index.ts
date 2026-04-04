export type Category =
    | 'tops'
    | 'bottoms'
    | 'dresses'
    | 'outerwear'
    | 'shoes'
    | 'accessories';

export interface ClothingItem {
    id: string;
    user_id: string;
    item_name: string;
    category: Category;
    season: string;
    color_primary: string;
    color_secondary?: string | null;
    pattern?: string | null;
    brand?: string | null;
    image_url: string;
    created_at: string;
}
