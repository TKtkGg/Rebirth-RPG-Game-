import styles from './FormInput.module.css';

type Props = {
    children: React.ReactNode;
    id: string;
    type: string;
    name: string;
    autoComplete: string;
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export const FormInput = (props: Props) => {
    const { children, id, type, name, autoComplete, value, onChange } = props;
    return(
        <div className={styles.formGroup}>
            <label htmlFor={id} className={styles.label}>
                {children}
            </label>
            <input 
                id={id} 
                type={type} 
                name={name} 
                autoComplete={autoComplete} 
                value={value} 
                onChange={onChange} 
                className={styles.input}
            />
        </div>
    )
}