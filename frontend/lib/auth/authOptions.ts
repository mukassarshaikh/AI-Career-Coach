/**
 * NextAuth configuration — authOptions.ts
 *
 * Credentials provider (email/password) for MVP.
 * Google OAuth slot is left in place but disabled until credentials are configured.
 *
 * Per frontend_architecture.md §7:
 *   - Session available via useSession() (client) or getServerSession() (server)
 *   - JWT strategy so the frontend can forward the token as a Bearer header to the backend
 *   - Backend validates the same JWT using the shared NEXTAUTH_SECRET
 */

import type { NextAuthOptions, User } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export const authOptions: NextAuthOptions = {
  // Use JWT strategy — the token is forwarded to the FastAPI backend as a Bearer token
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },

  pages: {
    signIn: "/login",
    error: "/login",
  },

  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email", placeholder: "you@example.com" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials): Promise<User | null> {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          // Forward credentials to the FastAPI backend for validation.
          // Phase 1 will implement POST /api/v1/auth/login on the backend.
          // For Phase 0 scaffolding we attempt the call; if the backend auth
          // route doesn't exist yet, we surface the error gracefully.
          const res = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });

          if (!res.ok) {
            return null;
          }

          const user = await res.json();
          // Expected shape: { id, email, name }
          return {
            id: user.id,
            email: user.email,
            name: user.name ?? null,
          };
        } catch {
          // Backend not yet running or auth route not yet implemented
          return null;
        }
      },
    }),

    // Google OAuth — slot reserved per frontend_architecture.md §7
    // Uncomment and set GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET in .env.local
    // GoogleProvider({
    //   clientId: process.env.GOOGLE_CLIENT_ID ?? "",
    //   clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
    // }),
  ],

  callbacks: {
    /**
     * Persist the user id into the JWT so the backend can look up the user.
     * The JWT is signed with NEXTAUTH_SECRET (HS256) — the FastAPI backend
     * validates it using the same secret (see backend/app/core/security.py).
     */
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.email = user.email;
        token.name = user.name;
      }
      return token;
    },

    async session({ session, token }) {
      if (token) {
        session.user.id = token.id as string;
        session.user.email = token.email as string;
        session.user.name = token.name as string | null;
      }
      return session;
    },
  },

  secret: process.env.NEXTAUTH_SECRET,
};
