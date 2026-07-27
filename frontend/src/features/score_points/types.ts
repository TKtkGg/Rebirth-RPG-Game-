export type ScorePointsCategory = {
    key: string;
    label: string;
};

export type ScorePointsStatItem = {
    key: string;
    label: string;
    current: string;
    next: string;
    card_class: string;
};

export type ScorePointsData = {
    categories: ScorePointsCategory[];
    category_key: string;
    stat_items: ScorePointsStatItem[];
    score_points: number;
};
