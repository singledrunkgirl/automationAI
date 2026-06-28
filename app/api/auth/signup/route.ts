import { NextRequest, NextResponse } from "next/server";
import { workos } from "@/app/api/workos";

export async function POST(req: NextRequest) {
  try {
    if (!process.env.WORKOS_API_KEY || !process.env.WORKOS_CLIENT_ID) {
      return NextResponse.json(
        { error: "WorkOS is not configured. Set WORKOS_API_KEY and WORKOS_CLIENT_ID." },
        { status: 503 }
      );
    }

    const { email, password, firstName, lastName } = await req.json();

    if (!email || !password) {
      return NextResponse.json(
        { error: "Email and password are required" },
        { status: 400 }
      );
    }

    if (password.length < 8) {
      return NextResponse.json(
        { error: "Password must be at least 8 characters" },
        { status: 400 }
      );
    }

    const user = await workos.userManagement.createUser({
      email,
      password,
      firstName: firstName || "",
      lastName: lastName || "",
      emailVerified: false,
    });

    try {
      await workos.userManagement.sendVerificationEmail({
        userId: user.id,
      });
    } catch (verifyErr) {
      console.warn("Failed to send verification email:", verifyErr);
    }

    return NextResponse.json({
      success: true,
      userId: user.id,
      message: "Account created. Check your email to verify.",
    });
  } catch (error: any) {
    console.error("Signup error:", error);

    if (error?.code === "user_already_exists") {
      return NextResponse.json(
        { error: "An account with this email already exists" },
        { status: 409 }
      );
    }

    return NextResponse.json(
      { error: error?.message || "Registration failed" },
      { status: 500 }
    );
  }
}
