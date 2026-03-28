"use client"

import { apiPost } from "../../lib/apiClient";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function SignUpScreen() {
    const router = useRouter();
    const [username, setUsername] = useState("");
    const [password1, setPassword1] = useState("");
    const [password2, setPassword2] = useState("");
    return(
        <div>
            <h1>サインアップ</h1>
            <div>
                <label>ユーザー名</label>
                <input type="text" name="username" value={username} onChange={(e) => setUsername(e.target.value)} />
            </div>
            <div>
                <label>パスワード</label>
                <input type="password" name="password1" value={password1} onChange={(e) => setPassword1(e.target.value)} />
            </div>
            <div>
                <label>パスワード（確認）</label>
                <input type="password" name="password2" value={password2} onChange={(e) => setPassword2(e.target.value)} />
            </div>
            <button onClick={() => {
                if (username === "" || password1 === "" || password2 === "") {
                    alert("ユーザー名とパスワードを入力してください");
                    return;
                }
                if (password1 !== password2) {
                    alert("パスワードとパスワード（確認）が一致しません");
                    return;
                }
                apiPost('/api/auth/signup/', {
                    username: username,
                    password1: password1,
                    password2: password2,
                }).then((data: { ok: boolean }) => {
                    if (data.ok) {
                        router.push('/game/start/');
                    }
                }).catch((error: { message: string }) => {
                    alert(error.message);
                });
            }}>サインアップ</button>
        </div>
    )
}