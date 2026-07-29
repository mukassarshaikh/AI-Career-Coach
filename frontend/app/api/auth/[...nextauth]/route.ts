/**
 * NextAuth dynamic route handler.
 * Placed at /app/api/auth/[...nextauth]/route.ts per Next.js App Router convention.
 */

import NextAuth from "next-auth";
import { authOptions } from "@/lib/auth/authOptions";

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
