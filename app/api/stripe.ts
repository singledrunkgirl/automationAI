import Stripe from "stripe";

let stripeInstance: Stripe | null = null;

export function getStripe(): Stripe {
  if (!stripeInstance) {
    const key = process.env.STRIPE_API_KEY || process.env.STRIPE_SECRET_KEY;
    if (!key) {
      throw new Error(
        "Stripe API key is missing. Set STRIPE_API_KEY or STRIPE_SECRET_KEY in your environment.",
      );
    }
    stripeInstance = new Stripe(key, {
      apiVersion: "2026-05-27.dahlia" as any,
    });
  }
  return stripeInstance;
}

// Backward-compatible export for routes that already use `stripe`
export const stripe = new Proxy({} as Stripe, {
  get(_target, prop) {
    const instance = getStripe();
    return (instance as any)[prop];
  },
});
