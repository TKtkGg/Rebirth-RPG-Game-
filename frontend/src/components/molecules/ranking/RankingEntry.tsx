import styles from "./RankingEntry.module.css";
import Image from "next/image";

type Props = {
    value: number;
    name: string;
    job_icon: string;
    job: string;
    className?: string;
};

export default function RankingEntry(props: Props) {
    const { value, name, job_icon, job, className } = props;
    return (
        <div className={`${styles.podiumEntry} ${className || ""}`}>
            <div className={styles.entryValue}>{value}</div>
            <div className={styles.entryName}>{name}</div>
            <Image
                src={job_icon}
                alt={job || "職業"}
                width={70}
                height={70}
                className={styles.entryIcon}
            />
        </div>
    );
}