"use client"

import { useEffect, useState } from "react";
import { apiGet } from "../../lib/apiClient";

export default function StartScreen() {
    const [data, setData] = useState<{ default_name: string, job_slots: { name: string }[] } | null>(null);
    useEffect(() => {
        apiGet('/api/start/').then((data: { default_name: string, job_slots: { name: string }[] }) => {
            setData(data);
        })
    }, []);
    return (
        <div>
            <h1>{data?.default_name}</h1>
            <h1>{data?.job_slots.map((job: { name: string }) => job.name).join(', ')}</h1>
        </div>
    )
}