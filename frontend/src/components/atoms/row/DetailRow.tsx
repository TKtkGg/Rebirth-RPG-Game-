import styles from './DetailRow.module.css';

type Props = {
    label: string;
    value: string | number;
}

export default function DetailRow(props: Props) {   
    const { label, value } = props;

    return (
        <div className={styles.detailStatItem}>
            <span>{label}:</span>
            <span>{value}</span>
        </div>
    );
}