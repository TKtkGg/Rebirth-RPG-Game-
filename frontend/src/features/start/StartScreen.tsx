"use client"

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { useRouter } from "next/navigation";

export default function StartScreen() {
    const router = useRouter();
    const [data, setData] = useState<{ default_name: string, job_slots: { name: string }[] } | null>(null);
    const [name, setName] = useState<string>("");
    const [selectedJob, setSelectedJob] = useState<string>("");
    useEffect(() => {
        apiGet('/api/start/').then((data: { default_name: string, job_slots: { name: string }[] }) => {
            setData(data);
        })
    }, []);
    return (
        <div>
            <input type="text" placeholder="名前を入力" value={name} onChange={(e) => setName(e.target.value)} />
            {data?.job_slots.map((job: {name: string}, index: number) =>
            (
                <button key={index} onClick={() => setSelectedJob(job.name)}>{job.name}</button>
            ))}
            <button onClick={() => {
                if (name === "" || selectedJob === "") {
                    alert("名前と職業を選択してください");
                    return;
                }
                apiPost('/api/start/', {
                    name: name,
                    job: selectedJob,
                }).then((data: { player_id: string }) => {
                    localStorage.setItem('player_id', data.player_id)
                    router.push(`/game/battle/home/${data.player_id}`);
                });
                
            }}>スタート</button>
        </div>
    )
}