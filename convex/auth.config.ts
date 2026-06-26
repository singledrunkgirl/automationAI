const clientId = process.env.WORKOS_CLIENT_ID ?? "";
const isProduction = process.env.NODE_ENV === "production";

const WORKOS_ISSUER_BASES = [
  "https://inclusive-family-82-staging.authkit.app",
  "https://auth.localhost:3006",
  "https://api.workos.com",
];

const WORKOS_AUDIENCES = Array.from(
  new Set(
    [
      clientId,
      "convex",
      "https://api.workos.com",
      "https://api.workos.com/",
      "https://api.workos.com/user_management",
      "https://api.workos.com/x/authkit",
      clientId
        ? `https://api.workos.com/user_management/${clientId}`
        : undefined,
      "https://auth.localhost:3006",
      "https://auth.localhost:3006/",
      "https://auth.localhost:3006/user_management",
      clientId
        ? `https://auth.localhost:3006/user_management/${clientId}`
        : undefined,
      ...(process.env.WORKOS_JWT_AUDIENCE?.split(",") ?? []),
    ]
      .filter((value): value is string => Boolean(value))
      .map((value) => value.trim())
      .filter(Boolean),
  ),
);

const normalizeBase = (base: string): string => base.replace(/\/+$/, "");

const WORKOS_AUTHKIT_ISSUER_VARIANTS = [
  "https://api.workos.com/x/authkit",
  "https://api.workos.com/x/authkit/",
];

const shouldAllowMissingAudienceForIssuer = (issuer: string): boolean => {
  // WorkOS User Management access tokens can be issued without aud/app_id.
  // Keep strict audience checks for other token types.
  return /\/user_management(\/|$)/.test(issuer);
};

const buildProvidersForBase = (base: string) => {
  const normalizedBase = normalizeBase(base);
  const jwks = `${normalizedBase}/sso/jwks/${clientId}`;

  const issuers = Array.from(
    new Set([
      `${normalizedBase}/`,
      normalizedBase,
      `${normalizedBase}/user_management`,
      `${normalizedBase}/user_management/${clientId}`,
      ...(normalizedBase === "https://api.workos.com"
        ? WORKOS_AUTHKIT_ISSUER_VARIANTS
        : []),
    ]),
  );

  return issuers.flatMap((issuer) => {
    const audienceScopedProviders = WORKOS_AUDIENCES.map((audience) => ({
      type: "customJwt" as const,
      issuer,
      algorithm: "RS256" as const,
      applicationID: audience,
      jwks,
    }));

    const permissiveProvider = shouldAllowMissingAudienceForIssuer(issuer)
      ? [
          {
            type: "customJwt" as const,
            issuer,
            algorithm: "RS256" as const,
            jwks,
          },
        ]
      : [];

    if (!isProduction) {
      return [
        {
          type: "customJwt" as const,
          issuer,
          algorithm: "RS256" as const,
          jwks,
        },
      ];
    }

    return [...permissiveProvider, ...audienceScopedProviders];
  });
};

const authConfig = {
  providers: clientId
    ? WORKOS_ISSUER_BASES.flatMap((base) => buildProvidersForBase(base))
    : [],
};

export default authConfig;
