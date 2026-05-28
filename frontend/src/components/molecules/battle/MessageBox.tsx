import styles from "./MessageBox.module.css";
import { useEffect, useRef } from "react";

type Props = {
    message: string;
    messageHistory: string[];
}

export const MessageBox = (props: Props) => {
    const { message, messageHistory } = props;
    const messageAreaRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        const el = messageAreaRef.current;
        if (!el) return;
        el.scrollTop = el.scrollHeight;
    }, [messageHistory]);
    return (
        <div className={styles.messageArea} ref={messageAreaRef}>
            <div className={styles.messageItem}>
                {message}
            </div>
        </div>
    )
};