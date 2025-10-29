'use client';

import React, { useState, useEffect, FormEvent } from 'react';
import {
  Plus,
  Briefcase,
  Users,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from '@/components/ui/table';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

interface JD {
  job_id: string;
  job_title: string;
  candidate_count: number;
  candidates_fetched: boolean;
  candidates_ranked: boolean;
}

interface JDForm {
  job_title: string;
  job_description: string;
}

interface APIResponse {
  message: string;
}

const JDParserUI: React.FC = () => {
  const [jdList, setJdList] = useState<JD[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [dialogOpen, setDialogOpen] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  const [formData, setFormData] = useState<JDForm>({
    job_title: '',
    job_description: '',
  });

  const router = useRouter();
  const API_BASE = 'http://localhost:8000/api';

  // Fetch JD list
  const fetchJDList = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE}/list`);
      if (!response.ok) throw new Error('Failed to fetch job listings');
      const data: JD[] = await response.json();
      setJdList(data);
    } catch (err: any) {
      setError(err.message || 'Unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJDList();
  }, []);

  // Handle form submit
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${API_BASE}/parse-jd`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to parse job description');
      }

      const result: APIResponse = await response.json();
      setSuccess(result.message);
      setFormData({ job_title: '', job_description: '' });

      setTimeout(() => {
        setDialogOpen(false);
        setSuccess('');
        fetchJDList();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Unexpected error occurred');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">
              Job Description Manager
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Parse and manage job descriptions with candidate tracking.
            </p>
          </div>

          {/* Add JD Dialog */}
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button size="lg" className="gap-2">
                <Plus className="w-5 h-5" />
                Add New JD
              </Button>
            </DialogTrigger>

            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Parse Job Description</DialogTitle>
                <DialogDescription>
                  Enter the job title and description to parse and store.
                </DialogDescription>
              </DialogHeader>

              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="job_title">Job Title</Label>
                  <Input
                    id="job_title"
                    placeholder="e.g., Senior Software Engineer"
                    value={formData.job_title}
                    onChange={(e) =>
                      setFormData({ ...formData, job_title: e.target.value })
                    }
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="job_description">Job Description</Label>
                  <Textarea
                    id="job_description"
                    placeholder="Paste the full job description here..."
                    value={formData.job_description}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        job_description: e.target.value,
                      })
                    }
                    rows={10}
                    required
                    className="max-h-[120px] overflow-y-auto resize-y"
                  />
                </div>

                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {success && (
                  <Alert>
                    <AlertDescription>{success}</AlertDescription>
                  </Alert>
                )}

                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setDialogOpen(false)}
                    disabled={submitting}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={submitting}>
                    {submitting ? 'Parsing...' : 'Parse & Save'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </header>

        {/* Job Listings Table */}
        <Card className="shadow-sm border rounded-2xl">
          <CardHeader className="flex flex-row items-center justify-between border-b">
            <div className="flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-muted-foreground" />
              <CardTitle>Job Listings</CardTitle>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchJDList}
              disabled={loading}
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </Button>
          </CardHeader>

          <CardContent>
            {loading && jdList.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center text-center">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mb-4"></div>
                <p className="text-sm text-muted-foreground">
                  Loading job descriptions...
                </p>
              </div>
            ) : jdList.length === 0 ? (
              <div className="py-12 flex flex-col items-center justify-center text-center">
                <Briefcase className="w-10 h-10 text-muted-foreground mb-3" />
                <p className="font-medium mb-1">No job descriptions yet</p>
                <p className="text-sm text-muted-foreground">
                  Click “Add New JD” to get started.
                </p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[300px]">Job Title</TableHead>
                    <TableHead>Job ID</TableHead>
                    <TableHead className="text-center">Candidates</TableHead>
                    <TableHead className="text-center">Fetched</TableHead>
                    <TableHead className="text-center">Ranked</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jdList.map((jd) => (
                    <TableRow
                      key={jd.job_id}
                      onClick={() => router.push(`/jobs/${jd.job_id}`)}
                      className="cursor-pointer hover:bg-muted/50 transition"
                    >
                      <TableCell className="font-medium flex items-center gap-2">
                        <Briefcase className="w-4 h-4 text-muted-foreground" />
                        {jd.job_title}
                      </TableCell>
                      <TableCell>
                        <code className="text-xs bg-muted px-2 py-1 rounded">
                          {jd.job_id.slice(0, 12)}...
                        </code>
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex items-center justify-center gap-2">
                          <Users className="w-4 h-4 text-muted-foreground" />
                          <span className="font-semibold">
                            {jd.candidate_count}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        {jd.candidates_fetched ? (
                          <Badge
                            variant="secondary"
                            className="bg-green-100 text-green-800"
                          >
                            <CheckCircle2 className="w-3 h-3 mr-1" /> Yes
                          </Badge>
                        ) : (
                          <Badge variant="outline">
                            <XCircle className="w-3 h-3 mr-1" /> No
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        {jd.candidates_ranked ? (
                          <Badge
                            variant="secondary"
                            className="bg-blue-100 text-blue-800"
                          >
                            <CheckCircle2 className="w-3 h-3 mr-1" /> Yes
                          </Badge>
                        ) : (
                          <Badge variant="outline">
                            <XCircle className="w-3 h-3 mr-1" /> No
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <footer className="text-center text-sm text-muted-foreground">
          Total Jobs:{' '}
          <span className="font-medium text-foreground">{jdList.length}</span>
        </footer>
      </div>
    </div>
  );
};

export default JDParserUI;
