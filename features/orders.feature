Feature: The orders service back-end
  As a Orders manager
  I need a RESTful order service
  So that I can keep track of all my orders

   Background:
    Given the following orders
      | customer_id | order_items                                 |
      | 101         | 1234,2,35.1,SHIPPED&3456,1,1000.2,DELIVERED |
      | 102         | 4567,3,5.60,CANCELLED                       |
      | 103         | 7890,10,10,PLACED                           |
      | 104         | 1000,10,10,DELIVERED                        |
      | 105         | 1,1,1,SHIPPED                               |

  Scenario: The Server is running
    When I visit the "Home Page"
    Then I should see "Order REST API Service" in the title
    And I should not see "404 Not Found"
