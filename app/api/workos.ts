import { WorkOS } from "@workos-inc/node";

let workosInstance: WorkOS | null = null;

const getWorkOS = (): WorkOS => {
  const apiKey = process.env.WORKOS_API_KEY;
  const clientId = process.env.WORKOS_CLIENT_ID;

  if (!apiKey || !clientId) {
    throw new Error(
      "WorkOS is not configured. Set WORKOS_API_KEY and WORKOS_CLIENT_ID.",
    );
  }

  workosInstance ??= new WorkOS(apiKey, { clientId });
  return workosInstance;
};

const workos = new Proxy({} as WorkOS, {
  get(_target, property, receiver) {
    const instance = getWorkOS();
    const value = Reflect.get(instance, property, receiver);
    return typeof value === "function" ? value.bind(instance) : value;
  },
});

export { getWorkOS, workos };
