import { Box } from "@/components/craft";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ResumePreviewProps {
  profileData: any;
  onGenerateResume: (theme: any) => void;
  isGenerating: boolean;
}

const ResumePreview = ({
  profileData,
  onGenerateResume,
  isGenerating,
}: ResumePreviewProps) => {
  const handleThemeChange = (value: string) => {
    const themeOptions = {
      modern: {
        primary_color: "0,0,0",
        accent_color: "100,100,100",
        font_family: "helvetica",
        section_style: "modern",
        layout: "modern",
        font_size: "11pt",
      },
      classic: {
        primary_color: "50,50,50",
        accent_color: "150,150,150",
        font_family: "times",
        section_style: "classic",
        layout: "traditional",
        font_size: "12pt",
      },
      minimal: {
        primary_color: "0,0,0",
        accent_color: "200,200,200",
        font_family: "helvetica",
        section_style: "basic",
        layout: "traditional",
        font_size: "10pt",
      },
    };

    onGenerateResume(themeOptions[value as keyof typeof themeOptions]);
  };

  return (
    <Box direction="col" gap={4} className="w-full max-w-4xl mx-auto">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Resume Preview</h3>
        <div className="flex gap-4">
          <Select onValueChange={handleThemeChange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Choose theme" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="modern">Modern Theme</SelectItem>
              <SelectItem value="classic">Classic Theme</SelectItem>
              <SelectItem value="minimal">Minimal Theme</SelectItem>
            </SelectContent>
          </Select>
          <Button disabled={isGenerating}>
            {isGenerating ? "Generating..." : "Download PDF"}
          </Button>
        </div>
      </div>

      <div className="border rounded-lg p-8 bg-white text-black min-h-[800px]">
        {/* Contact Section */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold mb-2">
            {profileData.contact?.name || ""}
          </h1>
          <p className="text-sm">
            {profileData.contact?.email} • {profileData.contact?.location}
          </p>
        </div>

        {/* Summary Section */}
        {profileData.summary && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold border-b mb-2">Summary</h2>
            <p className="text-sm">{profileData.summary}</p>
          </div>
        )}

        {/* Experience Section */}
        {profileData.experience && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold border-b mb-2">Experience</h2>
            {profileData.experience.map((exp: any, index: number) => (
              <div key={index} className="mb-4">
                <div className="flex justify-between">
                  <strong>{exp.title}</strong>
                  <span className="text-sm">
                    {exp.dates.start} - {exp.dates.end}
                  </span>
                </div>
                <div className="text-sm">{exp.company}</div>
                <p className="text-sm mt-1">{exp.description}</p>
              </div>
            ))}
          </div>
        )}

        {/* Education Section */}
        {profileData.education && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold border-b mb-2">Education</h2>
            {profileData.education.map((edu: any, index: number) => (
              <div key={index} className="mb-2">
                <div className="flex justify-between">
                  <strong>{edu.school}</strong>
                  <span className="text-sm">
                    {edu.dates.start} - {edu.dates.end}
                  </span>
                </div>
                <div className="text-sm">
                  {edu.degree} in {edu.field}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Box>
  );
};

export default ResumePreview;
