export const isValidEmail = (email: string) => /.+@.+\..+/.test(email);

export const isValidPhoneNumber = (phone: string) => /^\+?\d{10,15}$/.test(phone);

export const isStrongPassword = (password: string) => password.length >= 8;
