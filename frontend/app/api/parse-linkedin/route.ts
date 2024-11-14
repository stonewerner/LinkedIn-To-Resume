import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();

    // Forward the request to your Flask backend
    const response = await fetch("http://localhost:5000/api/parse-linkedin", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in parse-linkedin route:", error);
    return NextResponse.json(
      { error: "Failed to process LinkedIn PDF" },
      { status: 500 }
    );
  }
}
