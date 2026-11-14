#include "RNNLib.H"
#include <cstdio>
#include <cstdlib>

int main() {
    // Use the RAW model (h2o2_nn.pt) with RNNLib normalization
    const char* model_path = "/home/cj/NN_Project/ml_chem/h2o2/h2o2_nn.pt";
    float x_mean[] = {1850.76f, 4.971f, 0.0522f, 0.0435f, 0.0458f, 0.0658f, 0.0541f, 0.1448f, 0.0428f, 0.0425f, 0.0424f, 0.4662f};
    float x_std[]  = {595.46f, 7.577f, 0.0744f, 0.0759f, 0.0748f, 0.0773f, 0.0716f, 0.0825f, 0.0778f, 0.0776f, 0.0778f, 0.0775f};
    float y_mean[] = {1.938e6f, -2.975e6f, 5.930e5f, 3.001e7f, 1.192e7f, 5.121e7f, -3.245e6f, -8.946e7f, 0.0f, 0.0f, 9.100e9f};
    float y_std[]  = {8.432e6f, 1.187e7f, 1.947e7f, 1.100e8f, 3.654e8f, 3.440e8f, 6.604e8f, 6.462e8f, 1.0f, 1.0f, 9.706e10f};

    RNNModel* model = rnn_load(model_path, x_mean, x_std, y_mean, y_std, 12, 11);
    if (!model) {
        printf("FAIL: rnn_load returned nullptr\n");
        return 1;
    }
    printf("Model loaded OK\n");

    // Test: 2 points, 12 features each
    float inputs[24] = {
        // T, P, Y_H2, Y_H, Y_O, Y_O2, Y_OH, Y_H2O, Y_HO2, Y_H2O2, Y_AR, Y_N2
        1200.0f, 1.0f, 0.0285f, 0.0f, 0.0f, 0.226f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.745f,
        2000.0f, 1.0f, 0.01f, 0.001f, 0.001f, 0.01f, 0.01f, 0.10f, 0.001f, 0.001f, 0.0f, 0.866f
    };
    float outputs[22] = {0};

    int ret = rnn_forward_batch(model, inputs, 2, outputs);
    if (ret != 0) {
        printf("FAIL: rnn_forward_batch returned %d\n", ret);
        return 1;
    }

    for (int i = 0; i < 2; i++) {
        printf("[%d] ", i);
        for (int j = 0; j < 11; j++) {
            printf("%.3e ", outputs[i*11 + j]);
        }
        printf("\n");
    }

    rnn_free(model);
    printf("PASS\n");
    return 0;
}
