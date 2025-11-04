const formatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 2,
});

export const formatCurrency = (amount: number) => formatter.format(amount);
