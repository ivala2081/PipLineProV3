import TrustTabContent from '../components/trust/TrustTabContent';
import PageLayout from '../components/layout/PageLayout';

export default function Trust() {
  return (
    <div className="p-6">
      <PageLayout theme="slate-blue" minHeightScreen={true}>
        <TrustTabContent />
      </PageLayout>
    </div>
  );
}


