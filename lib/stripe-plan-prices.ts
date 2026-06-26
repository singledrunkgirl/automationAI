import type Stripe from "stripe";

type PlanPriceConfig = {
  productName: string;
  plan: string;
  interval: "month" | "year";
  unitAmount: number;
};

const PLAN_PRICE_CONFIG: Record<string, PlanPriceConfig> = {
  "pro-monthly-plan": {
    productName: "HackWithAI v2 Pro",
    plan: "pro",
    interval: "month",
    unitAmount: 25_00,
  },
  "pro-yearly-plan": {
    productName: "HackWithAI v2 Pro",
    plan: "pro",
    interval: "year",
    unitAmount: 21_00 * 12,
  },
  "pro-plus-monthly-plan": {
    productName: "HackWithAI v2 Pro+",
    plan: "pro-plus",
    interval: "month",
    unitAmount: 60_00,
  },
  "pro-plus-yearly-plan": {
    productName: "HackWithAI v2 Pro+",
    plan: "pro-plus",
    interval: "year",
    unitAmount: 50_00 * 12,
  },
  "ultra-monthly-plan": {
    productName: "HackWithAI v2 Ultra",
    plan: "ultra",
    interval: "month",
    unitAmount: 200_00,
  },
  "ultra-yearly-plan": {
    productName: "HackWithAI v2 Ultra",
    plan: "ultra",
    interval: "year",
    unitAmount: 166_00 * 12,
  },
};

export async function getOrCreateStripePrice(
  stripe: Stripe,
  lookupKey: string,
): Promise<Stripe.Price> {
  const existingPrices = await stripe.prices.list({
    active: true,
    lookup_keys: [lookupKey],
    limit: 1,
  });
  const existingPrice = existingPrices.data[0];
  if (existingPrice) return existingPrice;

  const config = PLAN_PRICE_CONFIG[lookupKey];
  if (!config) {
    throw new Error(`Unsupported subscription plan: ${lookupKey}`);
  }

  const product = await stripe.products.create({
    name: config.productName,
    metadata: {
      plan: config.plan,
      lookupKey,
    },
  });

  return stripe.prices.create({
    currency: "usd",
    lookup_key: lookupKey,
    product: product.id,
    recurring: {
      interval: config.interval,
    },
    unit_amount: config.unitAmount,
    metadata: {
      plan: config.plan,
      lookupKey,
    },
  });
}
