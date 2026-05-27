export type ItemScreenData = {
    id: number;
    name: string;
    target: string;
    effect_amount: number;
    price: number;
    description: string;
    current_stock: number;
    max_stock: number;
}

export type InventoryItemData = {
    id: number;
    item: ItemScreenData;
    quantity: number;
}