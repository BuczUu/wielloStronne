import random
import matplotlib.pyplot as plt

class SecureSumProtocol:
    def __init__(self, num_nodes, N=1000):
        self.num_nodes = num_nodes
        self.N = N   # wartość w której mieści się suma wszystkich nodów
        self.values = [random.randint(0, 100) for _ in range(num_nodes)]

    def real_world_execution(self, initiator_id=0):
        R = random.randint(1, self.N - 1)
        transcript = []

        y_current = (self.values[initiator_id] + R) % self.N
        transcript.append(y_current)

        for i in range(1, self.num_nodes):
            node_id = (initiator_id + i) % self.num_nodes
            y_current = (self.values[node_id] + y_current) % self.N
            transcript.append(y_current)

        return transcript

    def ideal_world_simulation(self):
        transcript = []

        for i in range(self.num_nodes):
            y_sim = random.randint(0, self.N - 1)
            transcript.append(y_sim)

        return transcript

    def honest_but_curious_view(self, node_id, initiator_id=0):
        """Returns the view of a specific node in real execution"""
        ring_pos = (node_id - initiator_id) % self.num_nodes

        R = random.randint(1, self.N - 1)
        y_current = (self.values[initiator_id] + R) % self.N

        for i in range(1, ring_pos):
            current_node = (initiator_id + i) % self.num_nodes
            y_current = (self.values[current_node] + y_current) % self.N

        y_incoming = y_current
        y_outgoing = (self.values[node_id] + y_incoming) % self.N

        return {
            'y_incoming': y_incoming,
            'y_outgoing': y_outgoing,
        }

    def ideal_world_view(self):
        return {
            'y_incoming': random.randint(0, self.N - 1),
            'y_outgoing': random.randint(0, self.N - 1),
        }


def statistical_test(real_samples, ideal_samples, num_bins=20):
    ax1 = plt.subplot(1, 1, 1)

    # Plot histograms
    ax1.hist(real_samples, bins=num_bins, alpha=0.7, label='Real World', color='blue')
    ax1.hist(ideal_samples, bins=num_bins, alpha=0.7, label='Ideal World', color='red')
    ax1.set_title('Distribution Comparison')
    ax1.set_xlabel('Message Value')
    ax1.set_ylabel('Frequency')
    ax1.legend()

    plt.tight_layout()
    plt.show()

def experiment_complete_transcripts():
    print("Complete Transcripts")
    protocol = SecureSumProtocol(num_nodes=10, N=1000)

    real_transcripts = []
    ideal_transcripts = []

    num_trials = 1000

    for _ in range(num_trials):
        real_transcript = protocol.real_world_execution()
        real_transcripts.extend(real_transcript)

        ideal_transcript = protocol.ideal_world_simulation()
        ideal_transcripts.extend(ideal_transcript)

    statistical_test(real_transcripts, ideal_transcripts)

def experiment_node_views():
    protocol = SecureSumProtocol(num_nodes=10, N=1000)

    node_id = 2
    real_views = []
    ideal_views = []

    num_trials = 1000

    for _ in range(num_trials):
        real_view = protocol.honest_but_curious_view(node_id)
        real_views.extend([real_view['y_incoming'], real_view['y_outgoing']])

        ideal_view = protocol.ideal_world_view()
        ideal_views.extend([ideal_view['y_incoming'], ideal_view['y_outgoing']])

    statistical_test(real_views, ideal_views)


if __name__ == "__main__":
    experiment_complete_transcripts()
    experiment_node_views()
