import styles from './HomeSubButton.module.css';
import Image from 'next/image';

type Props = {
    label: string;
    iconPath: string;
    onClick?: () => void;
    disabled?: boolean;
}

export const HomeSubButton = (props: Props) => {
    const { label, iconPath, onClick, disabled } = props;
    return(
        <button
            type="button"
            className={[styles.quickActionButton, disabled ? styles.disabled : ""].join(" ").trim()}
            aria-label={label}
            onClick={onClick ?? undefined}
            disabled={disabled ?? false}
        >
            <Image src={iconPath} alt={label} width={40} height={40} />
        </button>
    )
}