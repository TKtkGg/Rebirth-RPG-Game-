"use client"

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { useRouter } from "next/navigation";
import { StartScreenData } from "./types";
import Image from "next/image";

export default function StartScreen() {
    const router = useRouter();
    const [data, setData] = useState<StartScreenData | null>(null);
    const [name, setName] = useState<string>("");
    const [selectedJob, setSelectedJob] = useState<string>("");
    useEffect(() => {
        apiGet('/api/start/').then((data: StartScreenData) => {
            setData(data);
            setName(data?.default_name || "");
        })
    }, []);
    return (
        <div>
            <input type="text" placeholder="名前を入力" value={name} onChange={(e) => setName(e.target.value)} />
            {data?.job_slots.map((job: StartScreenData["job_slots"][number], index: number) =>
            (
                <button key={index} onClick={() => setSelectedJob(job.name)}>
                    <Image src={job.icon} alt={job.name} />
                    <p>{job.name}</p>
                    <p>{job.description}</p>
                    <p>{job.bonus}</p>
                    <p>{job.unlocked ? "開放" : "未開放"}</p>
                </button>
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
                    const playerId = data.player_id;
                    localStorage.setItem('playerId', playerId)
                    router.push(`/game/battle/home/${playerId}`);
                });
                
            }}>スタート</button>
        </div>
    )
}