'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Image from 'next/image';
import {
  Card,
  CardHeader,
  CardContent,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, Github, Mail } from 'lucide-react';

// ---------------------------------------------
// Candidate Card Component
// ---------------------------------------------
interface CandidateCardProps {
  candidate: any;
  showRank: boolean;
}

const CandidateCard: React.FC<CandidateCardProps> = ({ candidate, showRank }) => (
  <Card className="border rounded-2xl shadow-sm hover:shadow-md transition">
    <CardHeader className="flex flex-row items-center justify-between">
      <div className="flex items-center space-x-3">
        <Image
          src={candidate.avatar_url || '/default-avatar.png'}
          alt={candidate.username}
          width={40}
          height={40}
          className="rounded-full"
        />
        <div>
          <a
            href={candidate.github_url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium hover:underline"
          >
            {candidate.name || candidate.username}
          </a>
          <p className="text-sm text-gray-500">
            {candidate.bio || 'No bio available'}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        {showRank && candidate.rank && (
          <span className="text-sm font-semibold text-blue-600">
            Rank #{candidate.rank}
          </span>
        )}
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            asChild
          >
            <a
              href={candidate.github_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1"
            >
              <Github className="w-4 h-4" />
              GitHub
            </a>
          </Button>
          {candidate.email && (
            <Button
              size="sm"
              variant="outline"
              asChild
            >
              <a
                href={`mailto:${candidate.email}`}
                className="flex items-center gap-1"
              >
                <Mail className="w-4 h-4" />
                Email
              </a>
            </Button>
          )}
        </div>
      </div>
    </CardHeader>

    <CardContent className="space-y-4">
      {candidate.score !== undefined && candidate.score !== null && (
        <p className="text-sm text-gray-600">
          <strong>Score:</strong> {candidate.score.toFixed(2)}
        </p>
      )}
      {candidate.reasoning && (
        <p className="text-gray-700">
          <strong>Reasoning:</strong> {candidate.reasoning}
        </p>
      )}
      {candidate.summary && (
        <p className="text-gray-700">
          <strong>Summary:</strong> {candidate.summary}
        </p>
      )}

      {candidate.skills?.length > 0 && (
        <div>
          <strong>Skills:</strong>
          <div className="flex flex-wrap gap-2 mt-2">
            {candidate.skills.slice(0, 10).map((skill: string, idx: number) => (
              <span
                key={`${skill}-${idx}`}
                className="text-xs bg-gray-100 border rounded-full px-2 py-1"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {candidate.top_repos?.length > 0 && (
        <div>
          <strong>Top Repositories:</strong>
          <ul className="list-disc list-inside mt-2 space-y-1">
            {candidate.top_repos.slice(0, 3).map((repo: any, idx: number) => (
              <li key={`${repo.url}-${idx}`}>
                <a
                  href={repo.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  {repo.name}
                </a>{' '}
                ⭐ {repo.stars}
              </li>
            ))}
          </ul>
        </div>
      )}
    </CardContent>
  </Card>
);

// ---------------------------------------------
// Main Job ID Page
// ---------------------------------------------
export default function JobDetailsPage() {
  const { id: jobId } = useParams();

  const [jobData, setJobData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [ranking, setRanking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch job details
  useEffect(() => {
    const fetchJob = async () => {
      try {
        setLoading(true);
        const res = await fetch(`http://localhost:8000/api/get-job/${jobId}`);
        if (!res.ok) throw new Error('Failed to fetch job data');
        const data = await res.json();
        setJobData(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (jobId) fetchJob();
  }, [jobId]);

  // Fetch candidates
  const handleFetchCandidates = async () => {
    try {
      setFetching(true);
      setError(null);
      const res = await fetch(`http://localhost:8000/api/search-candidates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: jobId }),
      });
      if (!res.ok) throw new Error('Failed to fetch candidates');
      const updated = await res.json();
      setJobData(updated);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setFetching(false);
    }
  };

  // Rank candidates
  const handleRankCandidates = async () => {
    try {
      setRanking(true);
      setError(null);
      const res = await fetch(`http://localhost:8000/api/rank-candidates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: jobId }),
      });
      if (!res.ok) throw new Error('Failed to rank candidates');
      const updated = await res.json();
      setJobData(updated);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setRanking(false);
    }
  };

  // Process and merge candidates
  const getMergedCandidates = () => {
    if (!jobData) return [];

    const candidates = jobData.candidates || [];
    const rankedCandidates = jobData.ranked_candidates || [];

    // If we have ranked candidates, merge with original candidates data
    if (rankedCandidates.length > 0) {
      // Create a map of original candidates by username for quick lookup
      const candidatesMap = new Map(
        candidates.map((c: any) => [c.username, c])
      );

      // Merge ranked candidates with original data
      return rankedCandidates.map((rankedCandidate: any, index: number) => {
        const originalCandidate = candidatesMap.get(rankedCandidate.username) || {};
        return {
          ...originalCandidate,
          ...rankedCandidate,
          rank: index + 1,
        };
      });
    }

    // If only candidates are fetched (not ranked yet)
    return candidates;
  };

  const mergedCandidates = getMergedCandidates();
  const hasCandidates = mergedCandidates.length > 0;
  const isRanked = jobData?.ranked_candidates?.length > 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <Loader2 className="animate-spin w-8 h-8 text-gray-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-red-600">
        <p>Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      {/* Job Header */}
      <div>
        <h1 className="text-3xl font-semibold">{jobData.title}</h1>
        <p className="text-gray-600 mt-2">
          {jobData.company || 'Unknown Company'}
        </p>
      </div>

      {/* Job Description */}
      <Card>
        <CardContent className="p-6">
          <h2 className="text-xl font-semibold mb-2">Job Description</h2>
          <p className="text-gray-700 whitespace-pre-line">
            {jobData.description}
          </p>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button
          onClick={handleFetchCandidates}
          disabled={fetching || jobData.candidates_fetched}
          variant={jobData.candidates_fetched ? 'outline' : 'default'}
        >
          {fetching && <Loader2 className="animate-spin mr-2 w-4 h-4" />}
          {jobData.candidates_fetched
            ? 'Candidates Fetched'
            : 'Fetch Candidates'}
        </Button>

        <Button
          onClick={handleRankCandidates}
          disabled={ranking || !jobData.candidates_fetched || jobData.candidates_ranked}
          variant={jobData.candidates_ranked ? 'outline' : 'default'}
        >
          {ranking && <Loader2 className="animate-spin mr-2 w-4 h-4" />}
          {jobData.candidates_ranked ? 'Candidates Ranked' : 'Rank Candidates'}
        </Button>
      </div>

      {/* Status Info */}
      {hasCandidates && (
        <div className="flex gap-2 text-sm">
          {jobData.candidates_fetched && (
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full">
              ✓ Candidates Fetched
            </span>
          )}
          {jobData.candidates_ranked && (
            <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full">
              ✓ Candidates Ranked
            </span>
          )}
        </div>
      )}

      {/* Candidates Section */}
      <div className="space-y-6">
        <h2 className="text-xl font-semibold">
          {isRanked
            ? `Ranked Candidates (${mergedCandidates.length})`
            : hasCandidates
            ? `Fetched Candidates (${mergedCandidates.length})`
            : 'Candidates'}
        </h2>

        {fetching || ranking ? (
          <div className="flex justify-center items-center py-10">
            <Loader2 className="animate-spin w-6 h-6 text-gray-500" />
            <p className="ml-2 text-gray-600">
              {fetching
                ? 'Fetching candidates from GitHub...'
                : 'Ranking candidates based on job requirements...'}
            </p>
          </div>
        ) : hasCandidates ? (
          <div className="space-y-4">
            {mergedCandidates.map((candidate: any) => (
              <CandidateCard
                key={candidate.username}
                candidate={candidate}
                showRank={isRanked}
              />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="p-8 text-center">
              <p className="text-gray-600">
                No candidates found yet. Click "Fetch Candidates" to begin searching.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}