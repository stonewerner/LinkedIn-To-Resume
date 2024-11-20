import { NextRequest, NextResponse } from "next/server";

export async function POST(
  request: NextRequest,
  { params }: { params: { profileId: string } }
) {
  try {
    const themeOptions = await request.json();

    const response = await fetch(
      `http://127.0.0.1:5000/api/generate-resume/${params.profileId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(themeOptions),
      }
    );

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    // Get the PDF file from the response
    const pdfBuffer = await response.arrayBuffer();

    // Return the PDF with appropriate headers
    return new NextResponse(pdfBuffer, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="resume_${params.profileId}.pdf"`,
      },
    });
  } catch (error) {
    console.error("Error in generate-resume route:", error);
    return NextResponse.json(
      {
        error:
          error instanceof Error ? error.message : "Failed to generate resume",
      },
      { status: 500 }
    );
  }
}
