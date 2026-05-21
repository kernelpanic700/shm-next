import { Metadata } from 'next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar, Play } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Billing Cycle - SHM Next Admin',
};

export default function BillingPage() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Billing Cycle</h2>
        <Button>
          <Play className="mr-2 h-4 w-4" />
          Run Billing Cycle
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Billing History</CardTitle>
          <CardDescription>View and manage billing cycles</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading billing cycles...</p>
        </CardContent>
      </Card>
    </div>
  );
}