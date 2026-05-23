export type RankingData = {
    "categories": {
        "key": string;
        "label": string;
    }[];
    "category": string;
    "entries": {
        "name": string;
        "value": number;
        "job": string;
        "job_icon": string;
    }[];
    "label": string;
    "player_id": number;
}