/*
 * SSTF IO Scheduler
 *
 * For Kernel 4.13.9
 */

#include <linux/blkdev.h>
#include <linux/elevator.h>
#include <linux/bio.h>
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/init.h>

/* SSTF data structure. */
struct sstf_data {
        struct list_head queue;
        sector_t current_sector;
};

static void sstf_merged_requests(struct request_queue *q, struct request *rq,
                                 struct request *next)
{
        list_del_init(&next->queuelist);
}

/* Esta função despacha o próximo bloco a ser lido. */
static int sstf_dispatch(struct request_queue *q, int force)
{
        struct sstf_data *nd = q->elevator->elevator_data;
        struct request *rq;
        struct request *selected = NULL;
        sector_t current_sector = nd->current_sector;
        sector_t selected_distance = 0;
        sector_t distance;
        char direction = 'R';

        /*
         * Procura na fila a requisição cujo setor esteja
         * mais próximo do setor atualmente atendido.
         */
        list_for_each_entry(rq, &nd->queue, queuelist) {
                if (blk_rq_pos(rq) >= current_sector)
                        distance = blk_rq_pos(rq) - current_sector;
                else
                        distance = current_sector - blk_rq_pos(rq);

                if (!selected || distance < selected_distance) {
                        selected = rq;
                        selected_distance = distance;
                }
        }

        if (selected) {
                list_del_init(&selected->queuelist);
                elv_dispatch_sort(q, selected);

                nd->current_sector = blk_rq_pos(selected);

                printk(KERN_INFO "[SSTF] dsp %c %llu\n",
                       direction, blk_rq_pos(selected));

                return 1;
        }

        return 0;
}

static void sstf_add_request(struct request_queue *q, struct request *rq)
{
        struct sstf_data *nd = q->elevator->elevator_data;
        char direction = 'R';

        list_add_tail(&rq->queuelist, &nd->queue);

        printk(KERN_INFO "[SSTF] add %c %llu\n",
               direction, blk_rq_pos(rq));
}

static int sstf_init_queue(struct request_queue *q, struct elevator_type *e)
{
        struct sstf_data *nd;
        struct elevator_queue *eq;

        eq = elevator_alloc(q, e);
        if (!eq)
                return -ENOMEM;

        nd = kmalloc_node(sizeof(*nd), GFP_KERNEL, q->node);
        if (!nd) {
                kobject_put(&eq->kobj);
                return -ENOMEM;
        }

        eq->elevator_data = nd;

        INIT_LIST_HEAD(&nd->queue);

        /* O disco começa no setor 0. */
        nd->current_sector = 0;

        spin_lock_irq(q->queue_lock);
        q->elevator = eq;
        spin_unlock_irq(q->queue_lock);

        return 0;
}

static void sstf_exit_queue(struct elevator_queue *e)
{
        struct sstf_data *nd = e->elevator_data;

        BUG_ON(!list_empty(&nd->queue));
        kfree(nd);
}

/* Infraestrutura dos drivers de IO Scheduling. */
static struct elevator_type elevator_sstf = {
        .ops.sq = {
                .elevator_merge_req_fn          = sstf_merged_requests,
                .elevator_dispatch_fn           = sstf_dispatch,
                .elevator_add_req_fn            = sstf_add_request,
                .elevator_init_fn               = sstf_init_queue,
                .elevator_exit_fn               = sstf_exit_queue,
        },
        .elevator_name = "sstf",
        .elevator_owner = THIS_MODULE,
};

/* Inicialização do driver. */
static int __init sstf_init(void)
{
        return elv_register(&elevator_sstf);
}

/* Finalização do driver. */
static void __exit sstf_exit(void)
{
        elv_unregister(&elevator_sstf);
}

module_init(sstf_init);
module_exit(sstf_exit);

MODULE_AUTHOR("Miguel Xavier / GrupoF");
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("SSTF IO scheduler");
