"use client"

import { useState, useEffect } from "react";
import { RankingData } from "./types";
import { apiGet } from "@/src/lib/apiClient";

type Props = {
    playerId: string;
}

export default function RankingScreen({ playerId }: Props) {
    const [rankingData, setRankingData] = useState<RankingData | null>(null);
    const [category, setCategory] = useState<string>("score");

    useEffect(() => {
        apiGet(`/api/ranking/${playerId}?category=${category}`)
            .then((data: RankingData) => {
                setRankingData(data);
            });
    }, [playerId, category]);

    return (
        <div>
            <div>
                {rankingData?.categories.map((category) => (
                    <button key={category.key} onClick={() => setCategory(category.key)}>
                        {category.label}
                    </button>
                ))}
                <h1>{rankingData?.label}</h1>
                {rankingData?.entries.map((entry) => (
                    <div key={entry.name}>
                        {entry.name}
                        <img src={entry.job_icon} alt={entry.job} />
                        {entry.value}
                    </div>
                ))}
            </div>
            
        </div>
    );
}