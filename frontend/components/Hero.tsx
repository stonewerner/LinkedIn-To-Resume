"use client";

import Image from "next/image";
import { useState } from "react";
import Balancer from "react-wrap-balancer";
import { Upload } from "lucide-react";

import { Section, Container } from "@/components/craft";
import { Button } from "@/components/ui/button";
import { Input } from "./ui/input";
import ResumePreview from "./ResumePreview";

import Logo from "@/public/next.svg";

const Hero = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [responseData, setResponseData] = useState<any>(null);
  const [showPreview, setShowPreview] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setResponseData(null);
    setShowPreview(false);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/parse-linkedin", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResponseData(data);
      setShowPreview(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to upload file. Please try again."
      );
    } finally {
      setIsUploading(false);
    }
  };

  const handleGenerateResume = async (theme: any) => {
    if (!responseData?.profile_id) return;

    setIsGenerating(true);
    try {
      const response = await fetch(
        `/api/generate-resume/${responseData.profile_id}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(theme),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to generate resume");
      }

      // Handle PDF download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `resume_${responseData.profile_id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate resume. Please try again."
      );
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Section>
      <Container className="flex flex-col items-center text-center">
        <Image
          src={Logo}
          width={172}
          height={72}
          alt="Company Logo"
          className="not-prose mb-6 dark:invert md:mb-8"
        />

        {!showPreview ? (
          <>
            <h1 className="!mb-0">
              <Balancer>Enter URL or Upload File</Balancer>
            </h1>
            <h3 className="text-muted-foreground">
              <Balancer>
                Provide either a direct URL to your content or upload a file
                from your device
              </Balancer>
            </h3>

            <div className="w-full max-w-md space-y-4 mt-6 md:mt-12">
              <div className="flex gap-2">
                <Input
                  type="text"
                  placeholder="Enter URL here..."
                  className="flex-1 px-4 py-2 rounded-md border border-input bg-background"
                />
                <Button>Submit</Button>
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">
                    Or
                  </span>
                </div>
              </div>

              <Button
                variant="outline"
                className="w-full relative"
                disabled={isUploading}
              >
                <Input
                  type="file"
                  className="absolute inset-0 h-full w-full opacity-0 cursor-pointer"
                  accept=".pdf"
                  onChange={handleFileUpload}
                />
                {isUploading ? (
                  <span>Uploading...</span>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Choose File
                  </>
                )}
              </Button>
            </div>
          </>
        ) : (
          <div className="w-full">
            <div className="flex justify-between items-center mb-8">
              <Button variant="ghost" onClick={() => setShowPreview(false)}>
                ← Back to Upload
              </Button>
            </div>
            <ResumePreview
              profileData={responseData.profile_data}
              onGenerateResume={handleGenerateResume}
              isGenerating={isGenerating}
            />
          </div>
        )}

        {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
      </Container>
    </Section>
  );
};

export default Hero;
