// kd_tree.cpp
// Simple implementation of a 2D k-d tree in C++
#include <algorithm>
#include <iostream>
#include <vector>

struct Point
{
    double x, y;
};

struct KDNode
{
    Point point;
    KDNode* left;
    KDNode* right;
    KDNode(const Point& pt) : point(pt), left(nullptr), right(nullptr)
    {
    }
};

KDNode* build_kd_tree(std::vector<Point>& points, int depth = 0)
{
    if (points.empty())
        return nullptr;
    int axis = depth % 2;
    auto cmp = [axis](const Point& a, const Point& b)
    {
        return axis == 0 ? a.x < b.x : a.y < b.y;
    };
    size_t median = points.size() / 2;
    std::nth_element(
        points.begin(),
        points.begin() + median,
        points.end(),
        cmp);
    KDNode* node = new KDNode(points[median]);
    std::vector<Point> left(points.begin(), points.begin() + median);
    std::vector<Point> right(points.begin() + median + 1, points.end());
    node->left  = build_kd_tree(left, depth + 1);
    node->right = build_kd_tree(right, depth + 1);
    return node;
}

void print_kd_tree(KDNode* node, int depth = 0)
{
    if (!node)
        return;
    std::cout << std::string(depth * 2, ' ') << "(" << node->point.x << ", "
              << node->point.y << ")\n";
    print_kd_tree(node->left, depth + 1);
    print_kd_tree(node->right, depth + 1);
}

int main()
{
    std::vector<Point> points =
        {{2, 3}, {5, 4}, 
        {9, 6}, {4, 7}, 
        {8, 1}, {7, 2}};
    KDNode* root = build_kd_tree(points);
    std::cout << "k-d tree (2D):\n";
    print_kd_tree(root);
    // Cleanup omitted for brevity
    return 0;
}
